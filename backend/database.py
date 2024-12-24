import os

import dotenv
import pymongo
from models import Ship
from pymongo import MongoClient

dotenv.load_dotenv()
env = os.getenv


def connect() -> MongoClient:
    return MongoClient(env("MONGO_CONN", "").format(db_password=env("MONGO_PASSWORD")))


def put(client, user_id, ships, session):
    db = client["archipelago"]
    collection = db["users"]

    ships = [ship.model_dump() for ship in ships]

    if collection.find_one({"id": user_id}):  # User exists
        collection.update_one(
            {"id": user_id}, {"$push": {"ships": {"$each": ships}}}, session=session
        )
    else:
        collection.insert_one({"id": user_id, "ships": ships}, session=session)


def get(client, user_id):
    db = client["archipelago"]
    collection = db["users"]

    return collection.find_one({"id": user_id})


def hard_dump(client, data: dict[str, list[Ship]]):
    db = client["archipelago"]
    collection = db["users"]

    for user_id, ships in data.items():
        collection.update_one({"id": user_id}, {"$set": {"ships": ships}})
