import os
import time
from contextlib import asynccontextmanager

import data_processing
import dotenv
from database import cleanup, connect, load_from_database
from fastapi import FastAPI
from fastapi.responses import RedirectResponse
from fastapi_utils.tasks import repeat_every

dotenv.load_dotenv()

mongo_client = None 
user_data = {}

INTERVAL = 60 * 30  # 30 minutes
LOAD_DATA = False

@asynccontextmanager
async def lifespan(_: FastAPI):
    global user_data, mongo_client
    mongo_client = connect(os.getenv("MONGO_CONN", ''), os.getenv("MONGO_PASSWORD", ''))
    if LOAD_DATA:
        data_processing.startup(mongo_client)
    user_data = {u.id: u for u in load_from_database(mongo_client)}

    await update_data()

    yield
    mongo_client.close()

app = FastAPI(lifespan=lifespan)

@app.get('/users')
async def get_users(page: int = 0):
    return {'users': list(user_data)[page * 10: min((page + 1) * 10, len(user_data))]}


@repeat_every(seconds=INTERVAL)
async def update_data():
    global user_data
    new_users = {}
    for chunk in data_processing.load_messages(10000, oldest=int(time.time()) - INTERVAL):
        data_processing.load(chunk, None, new_users)

    data_processing.handle_new_data(mongo_client, new_users.values())
    cleanup(mongo_client, new_users.values())
    
@app.get('/me')
async def get_user_data(user_id: str):
    # [1:] is used to remove the 'U' prefix
    return user_data[user_id[1:]].model_dump()

@app.get('/force-cleanup')
async def force_cleanup(password: str):
    if password == os.getenv('MONGO_PASSWORD'):
        cleanup(mongo_client)
        return {'ok': True}

    return {'ok': False, 'error': 'Invalid password'}

@app.get('/auth')
async def auth_user(code: str):
    data = data_processing.auth_user(code)
    return RedirectResponse(f'https://archipelago.tathya.hackclub.app?tok={data["id_token"]}')
