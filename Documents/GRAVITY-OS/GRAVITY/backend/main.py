import asyncio
import json as _json
from contextlib import asynccontextmanager
from datetime import datetime, timezone

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from jose import JWTError, jwt

from backend.database import init_db
from backend.config import get_settings
from backend.routers import auth, onboarding, goals, habits, nudges, device, integrations, review, analytics, push
from backend.services.connection_manager import manager
from backend.workers.scheduler import scheduler

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    print("Starting Gravity API...")
    await init_db()
    print("Database tables created.")
    scheduler.start()
    print("Scheduler started.")
    yield
    scheduler.shutdown()
    print("Shutting down Gravity API.")


app = FastAPI(
    title="Gravity API",
    description="AI-powered goal tracking device backend",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(onboarding.router)
app.include_router(goals.router)
app.include_router(habits.router)
app.include_router(nudges.router)
app.include_router(device.router)
app.include_router(integrations.router)
app.include_router(review.router)
app.include_router(analytics.router)
app.include_router(push.router)


@app.get("/")
async def root():
    return {"name": "Gravity API", "version": "0.1.0", "status": "running", "docs": "/docs"}


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.websocket("/ws/{user_id}")
async def websocket_endpoint(websocket: WebSocket, user_id: int, token: str = ""):
    """
    Persistent WebSocket connection per user.
    Auth: JWT passed as ?token= query param (WebSocket can't send headers).
    Events emitted: LAYOUT_UPDATE, NUDGE, HABIT_COMPLETED, HEARTBEAT
    Events received: NUDGE_ACKNOWLEDGED, HABIT_COMPLETED (from device), HEARTBEAT
    """
    # Validate JWT
    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
        token_user_id = int(payload.get("sub"))
        if token_user_id != user_id:
            await websocket.close(code=4001)
            return
    except (JWTError, TypeError, ValueError):
        await websocket.close(code=4001)
        return

    await manager.connect(user_id, websocket)
    try:
        # Send initial HEARTBEAT on connect
        await manager.send_to_user(user_id, "HEARTBEAT", {
            "ts": datetime.now(tz=timezone.utc).isoformat(),
            "connected": True,
        })

        while True:
            try:
                data = await asyncio.wait_for(websocket.receive_text(), timeout=60.0)
                try:
                    msg = _json.loads(data)
                    event = msg.get("event")
                    if event == "HEARTBEAT":
                        await manager.send_to_user(user_id, "HEARTBEAT", {
                            "ts": datetime.now(tz=timezone.utc).isoformat(),
                        })
                    # NUDGE_ACKNOWLEDGED handled via REST PUT /nudges/{id}/acknowledge
                except Exception:
                    pass
            except asyncio.TimeoutError:
                # No message in 60s — send server heartbeat
                await manager.send_to_user(user_id, "HEARTBEAT", {
                    "ts": datetime.now(tz=timezone.utc).isoformat(),
                })
    except WebSocketDisconnect:
        manager.disconnect(user_id, websocket)
