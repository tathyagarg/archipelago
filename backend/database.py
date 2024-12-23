from models import *
from pymongo import MongoClient  # pyright: ignore


def connect(conn: str, password: str):
    try:
        client = MongoClient(conn.format(db_password=password))
        client.admin.command("ping")

        return client
    except Exception as e:
        raise Exception("Could not connect to MongoDB") from e


def add_to_database(client, users: list[User], session=None):
    db = client["archipelago"]
    collection = db["users"]

    collection.insert_many([user.model_dump() for user in users], session=session)


def load_from_database(client) -> dict[str, User]:
    db = client["archipelago"]
    collection = db["users"]
    res = {}

    for user in collection.find():
        res[user["id"]] = User(**user)

    return res


def update_database(client, user_id: str, ships: list[Ship], session=None):
    db = client["archipelago"]
    collection = db["users"]

    update_operation = {
        "$push": {"ships": {"$each": [ship.model_dump() for ship in ships]}}
    }
    filter = {"id": user_id}

    collection.update_one(filter, update_operation, session=session)


def hard_update(client, user_id: str, ships: list[Ship], session=None):
    db = client["archipelago"]
    collection = db["users"]

    update_operation = {"$set": {"ships": [ship.model_dump() for ship in ships]}}
    filter = {"id": user_id}

    collection.update_one(filter, update_operation, session=session)


def big_update(client, users: dict[str, User]):
    with client.start_session() as session:
        try:
            session.with_transaction(
                lambda session: [
                    hard_update(client, user_id, user.ships, session=session)
                    for user_id, user in users.items()
                ]
            )
        except Exception as e:
            raise Exception("Big update failed") from e


def handle_new_data(client, data: dict[str, dict[str, User | dict[str, list[Update]]]]):
    present_users = load_from_database(client)

    new_users: list[User] = []
    updated_users: dict[str, User] = {}

    # Use a conventional for-loop instead of 2 list-comps to avoid iterating over the same data twice
    for uid, user_data in data.items():
        user: User = user_data["user"]  # pyright: ignore
        if user.id in present_users:  # pyright: ignore
            user.ships.extend(user.ships)
            updated_users[uid] = user
        else:
            new_users.append(user)

        for ship in user.ships:
            updates: list[Update] = user_data["updates"].get(  # pyright: ignore
                ship.name, []
            )
            ship.updates.extend(updates)

    if updated_users:
        big_update(client, updated_users)
    if new_users:
        add_to_database(client, new_users)
