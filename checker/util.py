import os
import re
import requests
import random
import string
import tempfile
from typing import Optional, Tuple
from logging import LoggerAdapter
import secrets
import json
import hashlib

class CSRFRefreshError(Exception):
    pass
 

from enochecker3 import Enochecker, PutflagCheckerTaskMessage, GetflagCheckerTaskMessage, HavocCheckerTaskMessage, ExploitCheckerTaskMessage, PutnoiseCheckerTaskMessage, GetnoiseCheckerTaskMessage, ChainDB, MumbleException, FlagSearcher
from enochecker3.utils import assert_equals, assert_in
from httpx import AsyncClient, Response, RequestError


service_port = 8010

def os_succ(code):
    if code != 0:
        raise Exception("Internal error os command failed!")

async def refresh_token(client: AsyncClient, url: str) -> str:
    try:
        response = await client.get(url)

        if 'csrftoken' in response.cookies:
            return response.cookies['csrftoken']
        return response.cookies['csrf']  

    except CSRFRefreshError:
        raise MumbleException(f"Error while requesting new token from {url}")



async def register_user(client: AsyncClient, logger: LoggerAdapter) -> Tuple[str,str,str]:

    username = secrets.token_hex(8)
    password = secrets.token_hex(8)
    first_name = secrets.token_hex(5)
    last_name = secrets.token_hex(5)
    email = secrets.token_hex(8) + "@" + secrets.token_hex(4) +"." +secrets.token_hex(3)
    key = hashlib.sha1(secrets.token_hex(5).encode('utf-8')).hexdigest()

    data={
        "username": username,
        "password1": password,
        "password2": password,
        "first_name": first_name,
        "last_name": last_name,
        "email": email,
        "cryptographic_key": key,
        "next/": "shop/",
        "csrfmiddlewaretoken": await refresh_token(client,"signup/")
    }

    print(f"BASE_URL: {client.base_url}")
    for key in data:
        print(f"{key}: {data[key]}")

    headers={
        "Referer": f"{client.base_url}/signup/"
    }

    try:
        response = await client.post("signup/",data=data,headers=headers,follow_redirects=True)
    except RequestError:    
        raise MumbleException(f"Error while registering user")
    print(f"REGISTER_STATUS_CODE: {response.status_code}")
    
    assert_equals(response.status_code, 200, "Registration failed")



#async def login(client: AsyncClient, logger: LoggerAdapter) -> None:
