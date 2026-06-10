import os
from pymongo import MongoClient, ASCENDING, DESCENDING
from dotenv import load_dotenv

load_dotenv()

client = MongoClient(os.getenv("MONGO_URI"))
db = client[os.getenv("DB_NAME")]

users = db["users"]
voice_entries = db["voice_entries"]
events = db["events"]


def create_indexes():
    users.create_index([("email", ASCENDING)], unique=True)
    voice_entries.create_index([("user_id", ASCENDING)])
    voice_entries.create_index([("session_id", ASCENDING)])
    voice_entries.create_index([("created_at", DESCENDING)])
    events.create_index([("user_id", ASCENDING), ("date", ASCENDING)], unique=True)


create_indexes()
