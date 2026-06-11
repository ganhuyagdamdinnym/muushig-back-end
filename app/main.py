from fastapi import FastAPI
from app.api import room
from app.api import user
from app.api import real_room          # ← нэм
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(room.router)
app.include_router(user.router)
app.include_router(real_room.router)   # ← нэм

@app.get("/")
def root():
    return {"message": "Server running"}