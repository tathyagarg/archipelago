import json
import os
import re
import traceback
from collections import defaultdict

import database
import dotenv
import slack_sdk as slack  # pyright: ignore
from models import *

dotenv.load_dotenv()
env = os.getenv

client = slack.WebClient(env("SLACK_TOKEN"))

# Number of ships we want
LIMIT = 10_000
CHANNEL = "C07UA18MXBJ"  # #high-seas-ships channel
ARRPHEUS = "U07NGBJUDRD"  # Arrpheus' user ID
UNMATCHED_PATH = ".data/unmatched_updates.json"

PER_PAGE = 999  # Slack recommends no more than 200 results at a time
SLACK_CLIENT_ID = env("SLACK_CLIENT_ID")
SLACK_CLIENT_SECRET = env("SLACK_CLIENT_SECRET")


def process_message(message: dict) -> tuple[str, str, Ship | Update] | None:
    """
    Processes a message and returns a tuple containing the ship name, author id and a corresponding ship or update.
    Returns None if the message is not a ship message (for whatever reason).
    """
    if message["text"] != "*_SHIPS AHOY!!_*":
        return

    blocks = message.get("blocks", None)
    if not blocks:
        return

    if len(blocks) == 2:
        main_content_block, preview_block = blocks
        preview = preview_block["image_url"]
    else:
        main_content_block = blocks[0]
        preview_container = main_content_block.get("accessory")
        preview = preview_container["image_url"] if preview_container else ""

    # Thank you regex101.com!
    match = re.match(
        r"\*(.*)\*(?: _\(Update \d+\)_)?\nBy <@(\w+)> \| <(.*)\|Repo> \| <(.*)\|Demo>\nMade in (\d+) hours?(?: _\(\d+ in total\)_\n\n_Update Description:_ (.+))?",
        main_content_block["text"]["text"],
    )
    if not match:
        return None

    ship_name, author_id, repo, demo, hours, update_description = match.groups()
    hours = int(hours)

    if update_description:
        update = Update(description=update_description, hours=int(hours))
        return ship_name, author_id, update
    else:
        ship = Ship(
            name=ship_name,
            preview=preview,
            repo=repo,
            demo=demo,
            hours=hours,
            updates=[],
        )
        return ship_name, author_id, ship


def load_ships(
    limit: int,
    unmatched_updates: dict[str, dict[str, list[Update]]],
    *,
    oldest: int = 1730419200,
    cursor: str = "",
) -> tuple[str, int, dict[str, list[Ship]]]:
    """
    Loads upto the specified number of ships into the database.
    Returns the next cursor, number of ships loaded and the queued ship creations.

    Discrepancies between the number of ships loaded and the number of ships stems from the fact that not every message in #high-seas-ships is a ship message from Arrpheus.
    Returns -1 if an error occurred.
    """
    # Dict of user_id to Ships
    queued_ship_creations: dict[str, list[Ship]] = defaultdict(list)
    try:
        messages_data = client.conversations_history(
            channel=CHANNEL, limit=limit, oldest=oldest, cursor=cursor
        )
        if not messages_data["ok"]:
            return "", -1, queued_ship_creations

        messages = messages_data["messages"]
        processed: int = 0

        for message in messages:
            if message["user"] != ARRPHEUS:
                continue

            results = process_message(message)
            if not results:
                continue

            ship_name, author_id, result = results
            if not unmatched_updates.get(author_id):
                unmatched_updates[author_id] = {}

            if not unmatched_updates[author_id].get(ship_name):
                unmatched_updates[author_id][ship_name] = []

            if isinstance(result, Update):
                unmatched_updates[author_id][ship_name].append(result)
            else:
                result.updates = unmatched_updates[author_id][ship_name]
                # They not unmatched no mo
                unmatched_updates[author_id][ship_name] = []

                queued_ship_creations[author_id].append(result)
            processed += 1
    except Exception:
        traceback.print_exc()
        return "", -1, queued_ship_creations

    try:
        return (
            messages_data["response_metadata"]["next_cursor"],
            processed,
            queued_ship_creations,
        )
    except TypeError:
        return "", -2, queued_ship_creations


class UnmatchedHandler:
    def __enter__(self):
        with open(UNMATCHED_PATH) as f:
            data = json.load(f)
            self.data = {
                author_id: {
                    ship_name: [Update(**ship_update) for ship_update in ship_updates]
                    for ship_name, ship_updates in ships.items()
                }
                for author_id, ships in data.items()
            }

            return self.data

    # I'm too cool to handle errors
    def __exit__(self, *_):
        with open(UNMATCHED_PATH, "w") as f:
            data = {
                author_id: {
                    ship_name: [
                        ship_update.model_dump() for ship_update in ship_updates
                    ]
                    for ship_name, ship_updates in ships.items()
                    if ship_updates
                }
                for author_id, ships in self.data.items()
            }

            json.dump(
                {k: v for k, v in data.items() if v},
                f,
                indent=4,
            )


def bulk_load(limit: int, oldest: int = 0, cursor: str = ""):
    left = limit

    mongo_client = database.connect()
    while left > 0:
        print(left)
        current = min(left, PER_PAGE)
        with UnmatchedHandler() as unmatched_updates:
            next_cursor, loaded, queued_ship_creations = load_ships(
                current, unmatched_updates, oldest=oldest, cursor=cursor
            )

        if loaded == -1:
            # Resilience
            return

        left -= loaded
        cursor = next_cursor

        with mongo_client.start_session() as session:
            session.with_transaction(
                lambda session: [
                    database.put(mongo_client, user_id, ships, session)
                    for user_id, ships in queued_ship_creations.items()
                ]
            )

        if loaded == -2:
            break

    clear_unmatched_updates(mongo_client)
    mongo_client.close()


def clear_unmatched_updates(mongo_client):
    queued_fixes: dict[str, list[Ship]] = {}
    with UnmatchedHandler() as unmatched_updates:
        for user, ships in unmatched_updates.items():
            user_data = database.get(mongo_client, user)
            if not user_data:
                continue

            for ship, updates in ships.items():
                for i, user_ship in enumerate(user_data["ships"]):
                    if user_ship["name"] == ship:

                        user_data["ships"][i]["updates"].extend(
                            [update.model_dump() for update in updates]
                        )
                        unmatched_updates[user][ship] = []

            queued_fixes[user] = user_data["ships"]

        database.hard_dump(mongo_client, queued_fixes)


def auth_user(code: str):
    return client.openid_connect_token(
        code=code,
        client_id=SLACK_CLIENT_ID,
        client_secret=SLACK_CLIENT_SECRET,
    )


def get_user(user_id: str):
    return client.users_profile_get(user=user_id)["profile"]


def clean_duplicate_updates():
    mongo_client = database.connect()
    with mongo_client.start_session() as session:
        user_data = database.get(mongo_client, ARRPHEUS)
        for ship in user_data["ships"]:
            ship["updates"] = list(
                {update["description"]: update for update in ship["updates"]}.values()
            )
        database.hard_dump(
            mongo_client, {ARRPHEUS: user_data["ships"]}, session=session
        )
    mongo_client.close()


if __name__ == "__main__":
    bulk_load(LIMIT)
    # clear_unmatched_updates(database.connect())
