import asyncio
from fastapi import WebSocket
import json


class ConnectionManager:
    def __init__(self):
        # Maps user_id → list of active WebSocket connections
        # A user can have multiple connections (device + app simultaneously)
        self.active: dict[int, list[WebSocket]] = {}

    async def connect(self, user_id: int, websocket: WebSocket):
        await websocket.accept()
        if user_id not in self.active:
            self.active[user_id] = []
        self.active[user_id].append(websocket)

    def disconnect(self, user_id: int, websocket: WebSocket):
        if user_id in self.active:
            try:
                self.active[user_id].remove(websocket)
            except ValueError:
                pass
            if not self.active[user_id]:
                del self.active[user_id]

    async def send_to_user(self, user_id: int, event: str, data: dict):
        """Broadcast an event to all active connections for a user."""
        if user_id not in self.active:
            return
        message = json.dumps({"event": event, "data": data})
        dead = []
        for ws in self.active[user_id]:
            try:
                await ws.send_text(message)
            except Exception:
                dead.append(ws)
        for ws in dead:
            self.disconnect(user_id, ws)

    def is_connected(self, user_id: int) -> bool:
        return bool(self.active.get(user_id))


# Singleton — imported everywhere that needs to broadcast
manager = ConnectionManager()
