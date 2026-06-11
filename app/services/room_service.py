import uuid
import random
from app.db.mongo import rooms
from app.utils.serializers import serialize_room

card_ids = list(range(1, 33))


def create_room():
    room_id = str(uuid.uuid4())

    shuffled = card_ids.copy()
    random.shuffle(shuffled)

    playerCards = []
    bot1Cards = []
    bot2Cards = []
    bot3Cards = []
    bot4Cards = []

    index = 0
    for _ in range(5):
        playerCards.append(shuffled[index]); index += 1
        bot1Cards.append(shuffled[index]); index += 1
        bot2Cards.append(shuffled[index]); index += 1
        bot3Cards.append(shuffled[index]); index += 1
        bot4Cards.append(shuffled[index]); index += 1

    topCard = shuffled[index]; index += 1
    remainingCards = shuffled[index:]

    room = {
        "roomId": room_id,
        "rounds": [
            {
                "roundNumber": 1,
                "playerCards": playerCards,
                "bot1Cards": bot1Cards,
                "bot2Cards": bot2Cards,
                "bot3Cards": bot3Cards,
                "bot4Cards": bot4Cards,
                "topCard": topCard,
                "playersPoints": {
                    "player": 15,
                    "bot1": 15,
                    "bot2": 15,
                    "bot3": 15,
                    "bot4": 15,
                },
                "remainingCards": remainingCards,
                "currentPlayer": random.randint(0, 4),
            }
        ],
        "status": "playing",
    }

    result = rooms.insert_one(room)
    room["_id"] = str(result.inserted_id)
    
    return serialize_room(room)


def _room_response(room: dict) -> dict:
    """roomId, status, сүүлийн round-ийг буцаана."""
    last_round = room["rounds"][-1]
    return {
        "roomId": room["roomId"],
        "status": room.get("status", "playing"),
        "round": last_round,
    }


def get_room(roomId: str):
    room = rooms.find_one({"roomId": roomId})
    if not room:
        return {"error": "Room not found"}
    return _room_response(room)


def change_room_round(roomId: str, tricks_won: dict) -> dict:
    """
    tricks_won: { "player": 2, "bot1": 1, "bot2": 0, "bot3": 1, "bot4": 1 }

    Оноо дүрэм:
      - өнжсөн (tricksWon = -1)  → оноо өөрчлөгдөхгүй
      - орсон, 0 гэр авсан       → +5 оноо (муушиглав)
      - орсон, N гэр авсан       → -N оноо
    Оноо 0 буюу доош → тоглогч тоглоомоос гарна (status: finished).
    """
    room = rooms.find_one({"roomId": roomId})
    if not room:
        return {"error": "Room not found"}

    last_round = room["rounds"][-1]
    old_points = last_round["playersPoints"]

    # Оноо тооцоол
    keys = ["player", "bot1", "bot2", "bot3", "bot4"]
    new_points = {}
    for key in keys:
        prev = old_points.get(key, 15)
        won = tricks_won.get(key, -1)  # -1 = өнжсөн
        if won == -1:
            new_points[key] = prev         # өнжсөн → өөрчлөгдөхгүй
        elif won == 0:
            new_points[key] = prev + 5    # 0 гэр → +5 (муушиглав)
        else:
            new_points[key] = prev - won  # N гэр → -N

    # Тоглоом дууссан эсэх шалга
    finished = any(v <= 0 for v in new_points.values())
    if finished:
        rooms.update_one(
            {"roomId": roomId},
            {"$set": {"status": "finished"}}
        )
        return {
            "status": "finished",
            "playersPoints": new_points,
        }

    # Шинэ round үүсгэ
    shuffled = card_ids.copy()
    random.shuffle(shuffled)

    p, b1, b2, b3, b4 = [], [], [], [], []
    idx = 0
    for _ in range(5):
        p.append(shuffled[idx]);  idx += 1
        b1.append(shuffled[idx]); idx += 1
        b2.append(shuffled[idx]); idx += 1
        b3.append(shuffled[idx]); idx += 1
        b4.append(shuffled[idx]); idx += 1

    top_card = shuffled[idx]; idx += 1
    remaining = shuffled[idx:]

    round_number = len(room["rounds"]) + 1
    # Dealer өмнөх dealer-ийн дараагийн тоглогч
    prev_dealer = last_round["currentPlayer"]
    new_dealer = (prev_dealer + 1) % 5

    new_round = {
        "roundNumber": round_number,
        "playerCards": p,
        "bot1Cards": b1,
        "bot2Cards": b2,
        "bot3Cards": b3,
        "bot4Cards": b4,
        "topCard": top_card,
        "playersPoints": new_points,
        "remainingCards": remaining,
        "currentPlayer": new_dealer,
    }

    rooms.update_one(
        {"roomId": roomId},
        {"$push": {"rounds": new_round}}
    )

    # Шинэ round-тай room-ийг буцаа
    updated_room = rooms.find_one({"roomId": roomId})
    return _room_response(updated_room)