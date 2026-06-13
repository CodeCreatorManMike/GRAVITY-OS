from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from backend.database import init_db
from backend.config import get_settings
from backend.routers import auth, onboarding, goals, habits, nudges

settings = get_settings()

@asynccontextmanager
async def lifespan(app: FastAPI):
    print("Starting Gravity API...")
    await init_db()
    print("Database tables created.")
    yield
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

@app.get("/")
async def root():
    return {"name": "Gravity API", "version": "0.1.0", "status": "running", "docs": "/docs"}

@app.get("/health")
async def health():
    return {"status": "ok"}
