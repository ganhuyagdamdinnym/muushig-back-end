from fastapi import APIRouter, HTTPException
from app.services.user_service import create_user,login_user,get_user
from app.models.user import UserSignUp, UserLogin # Дээр үүсгэсэн моделийг импортлох

router = APIRouter(prefix="/user")

@router.post("/create_user")
def create(payload: UserSignUp):
    # payload.model_dump() нь pydantic объектыг dict болгож хувиргана
    result = create_user(payload.model_dump())
    
    if result["status"] == "error":
        raise HTTPException(status_code=400, detail=result["message"])
        
    return result

@router.post("/login")
def login(payload: UserLogin):
    result = login_user(payload.model_dump())
    
    if result["status"] == "error":
        raise HTTPException(status_code=401, detail=result["message"])
        
    return result

@router.get("/{userId}")
def getUserName(userId:str):
    return get_user(userId)