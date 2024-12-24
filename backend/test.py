import os

import dotenv
from slack_sdk import WebClient  # pyright: ignore

dotenv.load_dotenv()

TOKEN = os.getenv("SLACK_TOKEN")
CHANNEL = "C07UA18MXBJ"

client = WebClient(token=TOKEN)
count = 0
cursor = ""

while True:
    res = client.conversations_history(
        channel=CHANNEL, limit=999, oldest=1730419200, cursor=cursor
    )
    count += len(res["messages"])
    if not res["has_more"]:
        break

    cursor = res["response_metadata"]["next_cursor"]

print(count)
