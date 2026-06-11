import uuid
from app.db.mongo import users

def create_user(user_data: dict):
    # Хэрэглэгчийн нэр давхцаж байгаа эсэхийг шалгах
    existing_user = users.find_one({"name": user_data["username"]})
    if existing_user:
        return {"status": "error", "message": "Тоглогчийн нэр бүртгэгдсэн байна."}

    user_id = str(uuid.uuid4())
    
    user = {
        "_id": user_id,
        "name": user_data["username"],
        "email": user_data["email"],
        "password": user_data["password"], # Бодит ажиллагаан дээр энд password-ийг hash хийх хэрэгтэй
        "rating": 1200
    }
    
    users.insert_one(user)
    return {"status": "success", "message": "Амжилттай бүртгүүллээ."}


def login_user(login_data: dict):
    # Хэрэглэгчийг нэрээр нь хайх
    existing_user = users.find_one({"name": login_data["username"]})

    if not existing_user:
        return {"status": "error", "message": "Тоглогчийн нэр олдсонгүй."}

    # MongoDB дата нь dict байдаг тул ["password"] гэж хандана
    if existing_user["password"] != login_data["password"]:
        return {"status": "error", "message": "Нууц үг буруу байна."}

    # Амжилттай бол хэрэглэгчийн ID-г string болгож буцаана
    return {
        "status": "success", 
        "message": "Амжилттай нэвтэрлээ.", 
        "user_id": str(existing_user["_id"])
    }

def get_user(userId: str):
    # 1. Сэрвэрээс '_id'-аар нь зөв хайх
    user_info = users.find_one({"_id": userId})

    # 2. Хэрэглэгч олдоогүй тохиолдлыг шийдэх
    if not user_info:
        return {"status": "error", "message": "Хэрэглэгч олдсонгүй."}

    # 3. Фронтенд рүү JSON хэлбэрээр датаг буцаах
    return {
        "id": user_info["_id"],
        "name": user_info["name"],
        "rating": user_info.get("rating", 1200) # Хэрэв rating байхгүй бол default-оор 1200
    }