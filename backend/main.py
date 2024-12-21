import os

import dotenv
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError

dotenv.load_dotenv()

TOKEN = os.getenv("SLACK_TOKEN")
DEBUG = os.getenv("DEBUG")

client = WebClient(token=TOKEN)
if DEBUG:
    CHANNEL = 'C086HKQFLHF'
    LIMIT = 2
else:
    CHANNEL = 'C07UA18MXBJ'
    LIMIT = 1000

try:
    result = client.conversations_history(channel=CHANNEL, limit=LIMIT)
    print(result)
except SlackApiError as e:
    print(e)
