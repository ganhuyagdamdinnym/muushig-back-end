from fastapi import WebSocket
from typing import Dict, List

class ConnectionManager:
    def __init__(self):
        # room_id → { user_id: WebSocket }
        self.rooms: Dict[str, Dict[str, WebSocket]] = {}

    async def connect(self, room_id: str, user_id: str, ws: WebSocket):
        # await ws.accept()
        if room_id not in self.rooms:
            self.rooms[room_id] = {}
        self.rooms[room_id][user_id] = ws

    def disconnect(self, room_id: str, user_id: str):
        if room_id in self.rooms:
            self.rooms[room_id].pop(user_id, None)
            if not self.rooms[room_id]:
                del self.rooms[room_id]

    async def broadcast(self, room_id: str, message: dict, exclude: str = None):
        """Room-д байгаа бүх тоглогчид мессеж илгээ (exclude-с бусад)."""
        if room_id not in self.rooms:
            return
        for uid, ws in list(self.rooms[room_id].items()):
            if uid != exclude:
                try:
                    await ws.send_json(message)
                except Exception:
                    self.disconnect(room_id, uid)

    async def send_to(self, room_id: str, user_id: str, message: dict):
        """Тодорхой тоглогчид мессеж илгээ."""
        ws = self.rooms.get(room_id, {}).get(user_id)
        if ws:
            try:
                await ws.send_json(message)
            except Exception:
                self.disconnect(room_id, user_id)

    def get_connected_users(self, room_id: str) -> List[str]:
        return list(self.rooms.get(room_id, {}).keys())


manager = ConnectionManager()