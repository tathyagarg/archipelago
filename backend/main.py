import os
import re

import dotenv
from pydantic import BaseModel
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError


class Update(BaseModel):
    description: str
    hours: int

class Ship(BaseModel):
    name: str

    # URLs
    repo: str
    demo: str
    preview: str

    hours: int
    updates: list[Update] = []

class User(BaseModel):
    id: str  # Slack User ID 
    name: str
    ships: list[Ship] = []

dotenv.load_dotenv(override=True)

ARRPHEUS = 'U07NGBJUDRD'

TOKEN = os.getenv("SLACK_TOKEN")
DEBUG = int(os.getenv("DEBUG"))

client = WebClient(token=TOKEN)
if DEBUG:
    CHANNEL = 'C086HKQFLHF'
    LIMIT = 2
else:
    CHANNEL = 'C07UA18MXBJ'
    LIMIT = 5 

cache = {}  # This will be a redis cache

def load_messages(left: int, cursor: str = None):
    if left == 0: return []

    try:
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

        return usable + load_messages(
            left = remainder + left - len(usable),
            cursor = result['response_metadata']['next_cursor']
        )
    except SlackApiError as e:
        print(e)

def make_ship(ship: dict) -> Ship:
    ship_text = ship['blocks'][0]['text']['text']
    ship_img = ship['blocks'][1]['image_url']

    match = re.match(
        r'\*(.+)\*( _\(Update (\d+)\)_)?\nBy <\@U(\w+)> \| <(.+)\|Repo> \| <(.+)\|Demo>\nMade in (\d+) hours( _\((\d+) in total\)_\n\n_Update Description:_ (.+))?',
        ship_text
    )
    print(repr(ship_text))

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
        print(groups)
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

result = load_messages(LIMIT)
for ship_message in result:
    ship_gen = make_ship(ship_message)
    ship_data = next(ship_gen)

    if isinstance(ship_data[1], str):
        user_id, ship_name = ship_data
        original_ship = cache.get(user_id, {}).get(ship_name)
        _, ship = ship_gen.send(original_ship)

        if user_id not in cache:
            cache[user_id] = {}
        cache[user_id][ship_name] = ship
    else:
        user_id, ship = ship_data
        if user_id not in cache:
            cache[user_id] = {}
        cache[user_id][ship.name] = ship

print(cache)
