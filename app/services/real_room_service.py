import uuid
import random
from app.db.mongo import db

real_rooms = db["real_rooms"]
card_ids = list(range(1, 33))

MAX_PLAYERS = 5


def _deal_cards():
    shuffled = card_ids.copy()
    random.shuffle(shuffled)

    slots = [[], [], [], [], []]
    idx = 0
    for _ in range(5):
        for s in range(5):
            slots[s].append(shuffled[idx])
            idx += 1

    top_card = shuffled[idx]
    idx += 1
    remaining = shuffled[idx:]
    return slots, top_card, remaining


def _new_round(player_slots: list, points: dict, round_number: int, prev_dealer: int):
    slots, top_card, remaining = _deal_cards()
    new_dealer = (prev_dealer + 1) % MAX_PLAYERS

    return {
        "roundNumber": round_number,
        "cards": slots,          # cards[0..4] → slot-уудын карт
        "topCard": top_card,
        "playersPoints": points,
        "remainingCards": remaining,
        "currentPlayer": new_dealer,
    }


def create_real_room(creator_user_id: str, creator_username: str) -> dict:
    """Шинэ real room үүсгэж creator-ийг slot 0-д оруулна."""
    room_id = str(uuid.uuid4())

    slots, top_card, remaining = _deal_cards()

    room = {
        "roomId": room_id,
        "status": "waiting",     # waiting | playing | finished
        "slots": [
            # slot бүр: user_id, username, is_bot, is_ready
            {"slotIndex": 0, "userId": creator_user_id, "username": creator_username, "isBot": False},
            {"slotIndex": 1, "userId": None, "username": None, "isBot": False},
            {"slotIndex": 2, "userId": None, "username": None, "isBot": False},
            {"slotIndex": 3, "userId": None, "username": None, "isBot": False},
            {"slotIndex": 4, "userId": None, "username": None, "isBot": False},
        ],
        "rounds": [
            {
                "roundNumber": 1,
                "cards": slots,
                "topCard": top_card,
                "playersPoints": {
                    "0": 15, "1": 15, "2": 15, "3": 15, "4": 15
                },
                "remainingCards": remaining,
                "currentPlayer": random.randint(0, 4),
            }
        ],
    }

    real_rooms.insert_one(room)
    return _room_response(room)


def join_real_room(room_id: str, user_id: str, username: str) -> dict:
    """
    Хоосон slot олж тоглогч оруулна.
    Бүх slot дүүрсэн буюу 2+ тоглогч байвал тоглоом эхэлнэ.
    """
    room = real_rooms.find_one({"roomId": room_id})
    if not room:
        return {"error": "Room not found"}
    if room["status"] != "waiting":
        return {"error": "Room already started"}

    # Аль хэдийн орсон эсэх
    for slot in room["slots"]:
        if slot["userId"] == user_id:
            return _room_response(room)

    # Хоосон slot олох
    empty_slot = next((s for s in room["slots"] if s["userId"] is None), None)
    if not empty_slot:
        return {"error": "Room is full"}

    real_rooms.update_one(
        {"roomId": room_id, "slots.slotIndex": empty_slot["slotIndex"]},
        {"$set": {
            "slots.$.userId": user_id,
            "slots.$.username": username,
        }}
    )

    updated = real_rooms.find_one({"roomId": room_id})
    return _room_response(updated)


def start_game(room_id: str) -> dict:
    """
    2+ хүн орсон үед тоглоом эхлүүлнэ.
    Хоосон slot-уудыг bot-оор дүүргэнэ.
    """
    room = real_rooms.find_one({"roomId": room_id})
    if not room:
        return {"error": "Room not found"}

    human_count = sum(1 for s in room["slots"] if s["userId"] is not None)
    if human_count < 2:
        return {"error": "Need at least 2 players"}

    # Хоосон slot-уудыг bot болго
    bot_names = ["Bot A", "Bot B", "Bot C", "Bot D", "Bot E"]
    bot_idx = 0
    updated_slots = []
    for slot in room["slots"]:
        if slot["userId"] is None:
            updated_slots.append({
                **slot,
                "userId": f"bot_{slot['slotIndex']}",
                "username": bot_names[bot_idx],
                "isBot": True,
            })
            bot_idx += 1
        else:
            updated_slots.append(slot)

    real_rooms.update_one(
        {"roomId": room_id},
        {"$set": {"slots": updated_slots, "status": "playing"}}
    )

    updated = real_rooms.find_one({"roomId": room_id})
    return _room_response(updated)


def get_real_room(room_id: str) -> dict:
    room = real_rooms.find_one({"roomId": room_id})
    if not room:
        return {"error": "Room not found"}
    return _room_response(room)


def get_waiting_rooms() -> list:
    """Нэгдэж болох waiting room-уудын жагсаалт."""
    rooms = real_rooms.find({"status": "waiting"})
    return [
        {
            "roomId": r["roomId"],
            "playerCount": sum(1 for s in r["slots"] if s["userId"] is not None),
            "players": [s["username"] for s in r["slots"] if s["userId"] is not None],
        }
        for r in rooms
    ]


def finish_round(room_id: str, tricks_won: dict) -> dict:
    """
    tricks_won: { "0": 2, "1": 1, "2": 0, ... }  ← slot index-ээр
    Өнжсөн slot-ийн key илгээхгүй → оноо хэвээр.
    """
    room = real_rooms.find_one({"roomId": room_id})
    if not room:
        return {"error": "Room not found"}
    # Аль хэдийн finished бол дахин боловсруулахгүй
    if room.get("status") == "finished":
        return {"status": "finished", "playersPoints": room["rounds"][-1]["playersPoints"]}

    last_round = room["rounds"][-1]
    old_points = last_round["playersPoints"]

    new_points = {}
    for i in range(MAX_PLAYERS):
        key = str(i)
        prev = old_points.get(key, 15)
        won = tricks_won.get(key)
        if won is None:
            new_points[key] = prev          # өнжсөн
        elif won == 0:
            new_points[key] = prev + 5      # муушиглав
        else:
            new_points[key] = prev - won

    finished = any(v <= 0 for v in new_points.values())
    if finished:
        real_rooms.update_one(
            {"roomId": room_id},
            {"$set": {"status": "finished"}}
        )
        return {"status": "finished", "playersPoints": new_points}

    # Шинэ round
    prev_dealer = last_round["currentPlayer"]
    round_number = len(room["rounds"]) + 1
    slots_list = [[] for _ in range(5)]
    slots_new, top_card, remaining = _deal_cards()
    new_round = {
        "roundNumber": round_number,
        "cards": slots_new,
        "topCard": top_card,
        "playersPoints": new_points,
        "remainingCards": remaining,
        "currentPlayer": (prev_dealer + 1) % MAX_PLAYERS,
    }

    real_rooms.update_one(
        {"roomId": room_id},
        {"$push": {"rounds": new_round}}
    )

    updated = real_rooms.find_one({"roomId": room_id})
    return _room_response(updated)


def _room_response(room: dict) -> dict:
    last_round = room["rounds"][-1]
    return {
        "roomId": room["roomId"],
        "status": room["status"],
        "slots": room["slots"],
        "round": last_round,
    }