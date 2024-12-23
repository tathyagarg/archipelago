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
    users = load_from_database(client)
    new_users = []
    length = len(users)
    target = affected or users
    ids = [user.id for user in target]

    for user in users:
        if user.id not in ids:
            continue

        if affected is None:
            target_user = user
        else:
            target_user = next((u for u in target if u.id == user.id))

        seen_ships = {}
        for ship in user.ships + target_user.ships:
            ship.updates = list(set(ship.updates))
            if ship.name not in seen_ships:
                seen_ships[ship.name] = ship
            else:
                for name, seen_ship in seen_ships.items():
                    if name == ship.name:
                        if len(ship.updates) == 0:
                            break
                        seen_ship.hours += ship.hours
                        seen_ship.updates += ship.updates
                        break

        user.ships = list(seen_ships.values())
        new_users.append(user)

    def updates(_client, session):
        for i, user in enumerate(new_users):
            print("Cleaned up {}/{}".format(i + 1, length))
            hard_update(_client, user.id, user.ships, session=session)

    with client.start_session() as session:
        updates(
            client,
            session=session,
        )
