from collections import defaultdict
from typing import Iterable

from models import *
from pymongo import MongoClient


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


def load_from_database(client) -> list[User]:
    db = client["archipelago"]
    collection = db["users"]

    return [User(**user) for user in collection.find()]


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


def big_update(client, user_ids: list[str], shipses: list[list[Ship]]):
    with client.start_session() as session:
        try:
            session.with_transaction(
                lambda session: [
                    update_database(client, user_id, ships, session=session)
                    for user_id, ships in zip(user_ids, shipses)
                ]
            )
        except Exception as e:
            raise Exception("Big update failed") from e


def handle_new_data(client, data: Iterable[User]):
    present_users = load_from_database(client)
    present_user_ids = [user.id for user in present_users]

    new_users = []
    update_user_ids = []
    update_user_ships = []

    # Use a conventional for-loop instead of 2 list-comps to avoid iterating over the same data twice
    for user in data:
        if user.id in present_user_ids:
            update_user_ids.append(user.id)
            update_user_ships.append(user.ships)
        else:
            new_users.append(user)

    print("New users:", new_users)
    print("Update users:", update_user_ids)
    print("Update ships:", update_user_ships)
    if update_user_ids:
        big_update(client, update_user_ids, update_user_ships)
    if new_users:
        add_to_database(client, new_users)


def cleanup(client, affected: Iterable[User] | None = None):
    target = affected or load_from_database(client)
    updates: list[tuple[str, list[Ship]]] = []

    for user in target:
        ships: dict[str, Ship] = {}
        queued_updates: dict[str, list[Update]] = defaultdict(list)
        # print(user.ships)
        for ship in user.ships:
            if len(ship.updates) == 0:
                ships[ship.name] = ship

        for ship in user.ships:
            queued_updates[ship.name].extend(ship.updates)

        for ship_name, qupdates in queued_updates.items():
            ships[ship_name].updates = qupdates
            ships[ship_name].hours = sum(update.hours for update in qupdates)

        user.ships = list(ships.values())
        updates.append((user.id, user.ships))

    def make_updates(session):
        for i, (user_id, ships) in enumerate(updates):
            print(f"Updating user {i + 1}/{len(updates)}", end="\r")
            hard_update(client, user_id, ships, session=session)

    with client.start_session() as session:
        try:
            session.with_transaction(make_updates)
        except Exception as e:
            raise Exception("Cleanup failed") from e
