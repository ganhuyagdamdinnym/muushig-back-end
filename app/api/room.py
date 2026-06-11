from fastapi import APIRouter
from app.services.room_service import create_room, get_room, change_room_round
from app.utils.serializers import serialize_room
from app.db.mongo import rooms

router = APIRouter(prefix="/room")


@router.post("/create")
def create():
    return create_room()


@router.get("/{roomId}")
def get(roomId: str):
    return get_room(roomId)


@router.post("/{roomId}/round")
def change_round(roomId: str, tricks_won: dict):
    """
    Body жишээ:
    {
      "player": 2,
      "bot1": 0,
      "bot2": 1,
      "bot3": 1,
      "bot4": 1
    }
    Өнжсөн тоглогчийн key-г илгээхгүй буюу -1 илгээнэ.
    """
    return change_room_round(roomId, tricks_won)