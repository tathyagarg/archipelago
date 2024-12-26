import os
import time
from contextlib import asynccontextmanager

import data_processing
import database
import dotenv
from cachetools import TTLCache  # pyright: ignore
from cachetools_async import cached  # pyright: ignore
from fastapi import FastAPI
from fastapi.responses import RedirectResponse
from fastapi_utils.tasks import repeat_every  # pyright: ignore
from models import User
from utils import perlin

dotenv.load_dotenv()

mongo_client = None
user_data = {}

INTERVAL = 60 * 30  # 30 minutes
LOAD_DATA = False

DEBUG = os.getenv('DEBUG', 'False').lower() == 'true'

@asynccontextmanager
async def lifespan(_: FastAPI):
    global user_data, mongo_client
    mongo_client = database.connect()
    if LOAD_DATA:
        data_processing.bulk_load(10000)

    if not DEBUG:
        await update_data()

    yield
    mongo_client.close()


app = FastAPI(lifespan=lifespan)


@app.get("/users")
async def get_users(page: int = 0):
    return {"users": list(user_data)[page * 10 : min((page + 1) * 10, len(user_data))]}


@repeat_every(seconds=INTERVAL)
async def update_data():
    data_processing.bulk_load(10000, oldest=int(time.time()) - INTERVAL)


@app.get("/me")
async def get_user_data(user_id: str):
    print(user_id)
    return User(**database.get(mongo_client, user_id)).model_dump()


@app.get("/island")
@cached(cache=TTLCache(maxsize=1000, ttl=60 * 30))
async def get_island_data(user_id: str):
    # Slack user IDs are alnums, so we can decode them from base 36
    return perlin.Perlin(seed=int(user_id, 36)).island()


@app.get("/auth")
async def auth_user(code: str):
    data = data_processing.auth_user(code)
    return RedirectResponse(
        f'https://archipelago.tathya.hackclub.app?tok={data["id_token"]}'
    )


@app.get("/slack")
async def get_pfp(user_id: str):
    return data_processing.get_user(user_id)


@app.get("/force-cleanup")
async def force_cleanup():
    data_processing.clean_duplicate_updates()
    return {"success": True}
