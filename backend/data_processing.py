import os
import re
from typing import Generator

import dotenv
# I know what's entering the namespace so it's fine to use wildcard import
from database import *
from models import *
from slack_sdk import WebClient  # pyright: ignore

dotenv.load_dotenv(override=True)

ARRPHEUS = "U07NGBJUDRD"

TOKEN = os.getenv("SLACK_TOKEN")
DEBUG = int(os.getenv("DEBUG", "1"))

SLACK_CLIENT_ID = os.getenv("SLACK_CLIENT_ID")
SLACK_CLIENT_SECRET = os.getenv("SLACK_CLIENT_SECRET")

client = WebClient(token=TOKEN)

# ifdef ahh
if DEBUG:
    CHANNEL = "C086HKQFLHF"
    LIMIT = 2
else:
    CHANNEL = "C07UA18MXBJ"
    LIMIT = 5000

cache: dict[str, dict[str, User | dict[str, list[Update]]]] = {}  # For loading
user_cache: dict[str, dict] = {}


def load_messages(
    left: int, oldest: int = 0, cursor: str | None = None
) -> Generator[list[dict], None, list[dict]]:  # pyright: ignore
    print(f"Loading {left} messages")
    if left <= 0:
        return []

    # The converstaions_history API has a limit of 999 messages per call
    remainder = 0
    if left > 999:
        remainder = left - 999
        left = 999

    result = client.conversations_history(
        channel=CHANNEL, oldest=oldest, limit=left, cursor=cursor
    )

    # To filter out messages from people other than Arrpheus
    usable: list[dict] = []
    for message in result["messages"]:
        if message["user"] == ARRPHEUS:
            usable.append(message)

    yield usable
    if len(usable) != 0:
        if result["response_metadata"] is None:
            return []
        yield from load_messages(
            left=remainder + left - len(usable),
            cursor=result["response_metadata"].get("next_cursor"),
        )
    else:
        return []


def make_ship(ship: dict) -> tuple[str, str, Ship | Update]:
    ship_text = ship["blocks"][0]["text"]["text"]
    ship_img = ship["blocks"][1]["image_url"]

    match = re.match(
        r"\*(.+)\*(?: _\(Update \d+\)\_)?\nBy <@U(\w+)> \| <(.*)\|Repo> \| <(.*)\|Demo>\nMade in (\d+) hours(?: _\(.*\)_)?(?:\n\n_Update Description:_ (.+))?",
        ship_text,
    )

    if not match:
        raise ValueError(f"Invalid ship message: {ship_text}")

    groups = match.groups()
    ship_name, user_id, repo, demo, hours, description = groups
    hours = int(hours)

    if description is None:  # Original ship
        return (
            user_id,
            ship_name,
            Ship(
                name=ship_name,
                repo=repo,
                demo=demo,
                preview=ship_img,
                hours=hours,
                updates=[],
            ),
        )
    else:
        return (
            user_id,
            ship_name,
            Update(
                description=description,
                hours=hours,
            ),
        )


def load(data, cache: dict[str, dict[str, User | dict[str, list[Update]]]]):
    """
    data: The response from slack from endpoint converstaions_history
    """
    for i, message in enumerate(data):
        print(f"{i}/{len(data)}", end="\r")
        if message["user"] != ARRPHEUS:  # Ensure we have a arrpheus message
            continue

        try:
            uid, ship_name, res = make_ship(message)
        except ValueError:
            continue  # Womp womp

        if uid not in cache:
            cache[uid] = {
                "user": User(id=uid, ships=[]),
                "updates": {},
            }

        user = cache[uid]["user"]

        if isinstance(res, Ship):
            if ship_name in cache[uid]["updates"]:  # pyright: ignore
                res.updates.extend(cache[uid]["updates"][ship_name])  # pyright: ignore
                del cache[uid]["updates"][ship_name]  # pyright: ignore
            user.ships.append(res)  # pyright: ignore
        else:
            if ship_name not in cache[uid]["updates"]:  # pyright: ignore
                cache[uid]["updates"][ship_name] = []  # pyright: ignore

            cache[uid]["updates"][ship_name].append(res)  # pyright: ignore

    print()


def startup(mongo_client):
    global cache
    for chunk in load_messages(LIMIT):
        load(chunk, cache)

    handle_new_data(mongo_client, cache)


def auth_user(code: str):
    return client.openid_connect_token(
        code=code, client_id=SLACK_CLIENT_ID, client_secret=SLACK_CLIENT_SECRET
    )


def get_user(user_id: str):
    if user_id in user_cache:
        return user_cache[user_id]

    user = client.users_profile_get(user=user_id)["profile"]
    user_cache[user_id] = user
    return user


def cleanup(client, affected: dict[str, User] | None = None):
    target = affected or load_from_database(mongo_client)

    for user in target.values():
        res_ships = {}
        for ship in user.ships:
            if ship.name not in res_ships:
                res_ships[ship.name] = ship

        user.ships = list(res_ships.values())

    big_update(client, target)


if __name__ == "__main__":
    mongo_client = connect(os.getenv("MONGO_CONN", ""), os.getenv("MONGO_PASSWORD", ""))
    # startup(mongo_client)
    cleanup(mongo_client)
