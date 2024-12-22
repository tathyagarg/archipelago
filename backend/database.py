from typing import Iterable

from models import *
from pymongo import MongoClient


def connect(conn: str, password: str):
    try:
        client = MongoClient(conn.format(db_password=password))
        client.admin.command('ping')

        return client
    except Exception as e:
        raise Exception("Could not connect to MongoDB") from e 

def add_to_database(client, users: list[User], session = None):
    db = client['archipelago']
    collection = db['users']

    collection.insert_many([
        user.model_dump() for user in users
    ], session=session)

def load_from_database(client) -> list[User]:
    db = client['archipelago']
    collection = db['users']

    return [User(**user) for user in collection.find()]

def update_database(client, user_id: str, ships: list[Ship], session = None):
    db = client['archipelago']
    collection = db['users']

    update_operation = {
        '$push': {'ships': {'$each': [ship.model_dump() for ship in ships]}}
    }
    filter = {'id': user_id}

    collection.update_one(filter, update_operation, session=session)

def hard_update(client, user_id: str, ships: list[Ship], session = None):
    db = client['archipelago']
    collection = db['users']

    update_operation = {
        '$set': {'ships': [ship.model_dump() for ship in ships]}
    }
    filter = {'id': user_id}

    collection.update_one(filter, update_operation, session=session)

def big_update(client, user_ids: list[str], shipses: list[list[Ship]]):
    with client.start_session() as session:
        try:
            for user_id, ships in zip(user_ids, shipses):
                session.with_transaction(
                    lambda session: update_database(
                        client,
                        user_id,
                        ships,
                        session=session
                    )
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

    if update_user_ids:
        big_update(client, update_user_ids, update_user_ships)
    if new_users:
        add_to_database(client, new_users)


def cleanup(client, affected: Iterable[User] | None = None):
    users = load_from_database(client)
    new_users = []
    length = len(users)

    for i, user in enumerate(list(*affected)):
        seen_ships = {}
        for ship in user.ships:
            if ship.name not in seen_ships:
                seen_ships[ship.name] = ship
            else:
                for name, seen_ship in seen_ships.items():
                    if name == ship.name:
                        seen_ship.hours += ship.hours
                        seen_ship.updates += ship.updates
                        break

        user.ships = list(seen_ships.values())
        new_users.append(user)

    with client.start_session() as session:
        for i, user in enumerate(new_users):
            print('Cleaned up {}/{}'.format(i + 1, length), end='\r')
            session.with_transaction(
                lambda session: hard_update(
                    client,
                    user.id,
                    user.ships,
                    session=session
                )
            )
