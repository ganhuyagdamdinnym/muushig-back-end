from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Header
from typing import Optional
from app.services.real_room_service import (
    create_real_room,
    join_real_room,
    start_game,
    get_real_room,
    get_waiting_rooms,
    finish_round,
)
from app.services.websocket_manager import manager

router = APIRouter(prefix="/real_room")


# ── HTTP endpoints ────────────────────────────────────────────────────────────

@router.get("/list")
def list_rooms():
    """Нэгдэж болох waiting room-уудын жагсаалт."""
    return get_waiting_rooms()


@router.post("/create")
def create(body: dict):
    """
    Body: { "userId": "...", "username": "..." }
    """
    return create_real_room(body["userId"], body["username"])


@router.post("/{roomId}/join")
def join(roomId: str, body: dict):
    """
    Body: { "userId": "...", "username": "..." }
    """
    return join_real_room(roomId, body["userId"], body["username"])


@router.post("/{roomId}/start")
def start(roomId: str):
    """2+ тоглогч байвал тоглоом эхлүүлнэ, bot дүүргэнэ."""
    return start_game(roomId)


@router.get("/{roomId}")
def get(roomId: str):
    return get_real_room(roomId)


@router.post("/{roomId}/round")
def end_round(roomId: str, tricks_won: dict):
    """
    Body: { "0": 2, "1": 0, "3": 1 }  ← өнжсөн slot-ийг орхино
    """
    return finish_round(roomId, tricks_won)


# ── WebSocket endpoint ────────────────────────────────────────────────────────

@router.websocket("/{roomId}/ws/{userId}")
async def websocket_endpoint(ws: WebSocket, roomId: str, userId: str):
    await manager.connect(roomId, userId, ws)

    # Бусад тоглогчдод мэдэгдэх
    await manager.broadcast(roomId, {
        "type": "player_joined",
        "userId": userId,
    }, exclude=userId)

    # Одоогийн room state-г шинэ тоглогчид илгээ
    room_data = get_real_room(roomId)
    await manager.send_to(roomId, userId, {
        "type": "room_state",
        "data": room_data,
    })

    try:
        while True:
            msg = await ws.receive_json()
            await _handle_message(roomId, userId, msg)
    except WebSocketDisconnect:
        manager.disconnect(roomId, userId)
        await manager.broadcast(roomId, {
            "type": "player_left",
            "userId": userId,
        })


async def _handle_message(room_id: str, user_id: str, msg: dict):
    msg_type = msg.get("type")

    if msg_type == "start_game":
        # Хэн нэгэн "эхлүүлэх" дарсан
        result = start_game(room_id)
        await manager.broadcast(room_id, {
            "type": "game_started",
            "data": result,
        })

    elif msg_type == "play_card":
        # { type: "play_card", card: {...}, slotIndex: 0 }
        await manager.broadcast(room_id, {
            "type": "card_played",
            "userId": user_id,
            "slotIndex": msg.get("slotIndex"),
            "card": msg.get("card"),
        }, exclude=user_id)

    elif msg_type == "decide":
        # { type: "decide", joining: true/false, slotIndex: 0 }
        await manager.broadcast(room_id, {
            "type": "player_decided",
            "userId": user_id,
            "slotIndex": msg.get("slotIndex"),
            "joining": msg.get("joining"),
        }, exclude=user_id)

    elif msg_type == "swap_cards":
        # { type: "swap_cards", slotIndex: 0, count: 2 }
        await manager.broadcast(room_id, {
            "type": "cards_swapped",
            "userId": user_id,
            "slotIndex": msg.get("slotIndex"),
            "count": msg.get("count"),
        }, exclude=user_id)

    elif msg_type == "end_round":
        # Зөвхөн slotIndex == 0 (эхний slot) дуудна — давхардлаас сэргийлэх
        slot_index = msg.get("slotIndex", -1)
        if slot_index != 0:
            return
        result = finish_round(room_id, msg.get("tricksWon", {}))
        await manager.broadcast(room_id, {
            "type": "round_ended",
            "data": result,
        })

    elif msg_type == "chat":
        # { type: "chat", text: "..." }
        await manager.broadcast(room_id, {
            "type": "chat",
            "userId": user_id,
            "text": msg.get("text"),
        }, exclude=user_id)