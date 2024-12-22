import os
import re
from typing import Generator

import dotenv
# I know what's entering the namespace so it's fine to use wildcard import
from database import *
from models import *
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError

dotenv.load_dotenv(override=True)

ARRPHEUS = 'U07NGBJUDRD'

TOKEN = os.getenv("SLACK_TOKEN")
DEBUG = int(os.getenv("DEBUG", '1'))

client = WebClient(token=TOKEN)

#ifdef ahh
if DEBUG:
    CHANNEL = 'C086HKQFLHF'
    LIMIT = 2
else:
    CHANNEL = 'C07UA18MXBJ'
    LIMIT = 5000 

cache: dict[str, User] = {}  # This will be a redis cache

def load_messages(left: int, cursor: str | None = None) -> Generator[list[dict], None, None]:
    print(f'Loading {left} messages')
    if left <= 0: yield []

    # The converstaions_history API has a limit of 100 messages per call
    remainder = 0
    if left > 100:
        remainder = left - 100
        left = 100

    result = client.conversations_history(channel=CHANNEL, limit=left, cursor=cursor)

    # To filter out messages from people other than Arrpheus
    usable = []
    for message in result['messages']:
        if message['user'] == ARRPHEUS:
            usable.append(message)

    yield usable
    yield from load_messages(
        left = remainder + left - len(usable),
        cursor = result['response_metadata']['next_cursor']
    )

def make_ship(ship: dict) -> Generator[tuple[str, str | Ship], Ship | None, None]:
    ship_text = ship['blocks'][0]['text']['text']
    ship_img = ship['blocks'][1]['image_url']

    match = re.match(
        r'\*(.+)\*( _\(Update (\d+)\)_)?\nBy <\@U(\w+)> \| <(.+)\|Repo> \| <(.+)\|Demo>\nMade in (\d+) hours( _\((\d+) in total\)_\n\n_Update Description:_ (.+))?',
        ship_text
    )
    if not match:
        raise ValueError(f"Invalid ship message: {ship_text}")

    groups = match.groups()

    if groups[1] is None:
        ship_name, _, _, user_id, repo, demo, hours, _, _, _ = groups
        hours = int(hours)

        yield (user_id, Ship(
            name = ship_name,
            repo = repo,
            demo = demo,
            preview = ship_img,
            hours = hours
        ))
    else:
        ship_name, _, update_no, user_id, repo, demo, hours, _, total_hours, description = groups
        description = description or ''
        hours = int(hours)

        original_ship = yield (user_id, ship_name)

        # Original Ship was not found
        if not original_ship:
            yield (user_id, Ship(
                name = ship_name,
                repo = repo,
                demo = demo,
                preview = ship_img,
                hours = hours,
                updates = [Update(description=description, hours=hours)]
            ))
        else:
            yield (user_id, Ship(
                name = original_ship.name,
                repo = original_ship.repo,
                demo = original_ship.demo,
                preview = original_ship.preview,
                hours = original_ship.hours,
                updates = [Update(description=description, hours=hours)] + original_ship.updates
            ))

def get_username(user_id: str) -> str:
    # `U + user_id` is the format Slack uses
    # Since we know all the user_ids will be for users, we can skip storing the first letter (U).
    result = client.users_profile_get(user='U' + user_id)
    return result['profile']['display_name']

def load(data, log_buf):
    for i, ship_message in enumerate(data):
        print(f'Loading ship {i + 1}/{len(data)}', end='\r')
        try:
            ship_gen = make_ship(ship_message)
            ship_data = next(ship_gen)
        except ValueError:
            log_buf.write(f"Invalid ship message: {ship_message['blocks'][0]['text']['text']}\n")
            continue
    
        if isinstance(ship_data[1], str):
            user_id, ship_name = ship_data
            user_ships = cache.get(user_id, User(id=user_id, name=get_username(user_id), ships=[])).ships

            original_ship = None
            for ship in user_ships:
                if ship.name == ship_name:
                    original_ship = ship
                    break

            _, ship = ship_gen.send(original_ship)
    
            if user_id not in cache:
                cache[user_id] = User(id=user_id, name=get_username(user_id), ships=[])
            cache[user_id].ships.append(ship) # pyright: ignore
        else:
            user_id, ship = ship_data

            if user_id not in cache:
                cache[user_id] = User(id=user_id, name=get_username(user_id), ships=[])
            cache[user_id].ships.append(ship) # pyright: ignore

    print()


def startup(mongo_client):
    global cache
    with open('logs', 'a') as log_buf:
        for chunk in load_messages(LIMIT):
            load(chunk, log_buf)
            handle_new_data(mongo_client, cache.values())
            cache = {}

if __name__ == '__main__':
    mongo_client = connect(os.getenv("MONGO_CONN", ''), os.getenv("MONGO_PASSWORD", ''))
    # startup(mongo_client)
    cleanup(mongo_client)
