

from pymongo import MongoClient
import os
from dotenv import load_dotenv

load_dotenv()

MONGO_URL = os.getenv("MONGO_URL")
# MONGO_URL = "mongodb+srv://<daimaa070423>:<daimaa07>@cluster0.fgp6xm2.mongodb.net/?appName=Cluster0"
client = MongoClient(MONGO_URL)

db = client["muushig"]

rooms = db["rooms"] 
users=db["users"]  