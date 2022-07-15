import os
import re
import random
import string
import tempfile
from logging import Logger, LoggerAdapter
import secrets
import json
import hashlib
from files import license_from_template
import string_utils
from datetime import datetime

from enochecker3 import ChainDB, MumbleException
from enochecker3.utils import assert_equals
from httpx import AsyncClient, RequestError
from errors import MisconfigurationError,Pixels_ShopItemError

service_port = 8010

email_providers = [
    "gmail",
    "outlook",
    "gmx",
    "web",
    "protonmail",
    "aol",
    "zohomail",
    "enowars",
    ]

email_endings = [
    "de",
    "com",
    "uk",
    "it",
    "org",
    "net",
    "edu",
    "gov"
]

def check_kwargs(func_name: str ,keys: list, kwargs,logger: LoggerAdapter): 
    logger.debug(f"{func_name.upper()} - KWARG-CONFIG : {kwargs}")
    for key in keys:
        if not kwargs[key]:
            logger.critical(f" {func_name} - Missing KEY {key}! ")
            raise MisconfigurationError(f"FUNC: {func_name} - Kwargs has no key <{key}> !")
        

     
async def register_user(client: AsyncClient, logger: LoggerAdapter,db: ChainDB,chain_id:int) -> dict:
    global email_providers,email_endings
    t0 = datetime.now()
    username = secrets.token_hex(12)
    password = secrets.token_hex(12)
    first_name = secrets.token_hex(5)
    last_name = secrets.token_hex(5)
    email = secrets.token_hex(8) + "@" + email_providers[secrets.randbelow(8)] +"." + email_endings[secrets.randbelow(8)]

    data={
        "username": username,
        "password1": password,
        "password2": password,
        "first_name": first_name,
        "last_name": last_name,
        "email": email,
    }

    headers={
        "Referer": f"{client.base_url}/signup/"
    }
    
    try:
        logger.debug(f"REQUESTURL: {client.base_url} signup/")
        response = await client.post("signup/",data=data,headers=headers,follow_redirects=True)
    except RequestError:    
        logger.error(f"ERROR - REGISTER USER: Could not register USER {username} no response {json.dumps(data)}")
        raise MumbleException("Error while registering user")
     
    if response.status_code != 200:
        logger.error(f"Registration failed: {json.dumps(data)}")
        raise MumbleException("Error while registering user")

    t1 = datetime.now()
    d1 = t1 - t0
    logger.debug(f"Time - register_user (post) {d1.total_seconds()} s")
    logger.info(f"Registered USER {username}")
    
    if chain_id:
        await db.set("user",{'username':username,'password':password})
    t2 = datetime.now()
    d2 = t2 - t1
    logger.debug(f"Time - register_user (DB_set) {d2.total_seconds()} s")
    logger.debug(f"REGISTER USER - Total time {(t2-t0).total_seconds()} s")
    return data

async def login(client: AsyncClient, logger: LoggerAdapter, db: ChainDB,kwargs) -> None:
    t0 = datetime.now()
    keys = ['username','password']
    check_kwargs(func_name=login.__name__,keys=keys,kwargs=kwargs,logger=logger)

    data={
        "username": kwargs['username'],
        "password": kwargs['password'],
        "next/": "shop/1/",
    }

    headers={
        "Referer": f"{client.base_url}/login/"
    }

    try:
        logger.debug(f"REQUESTURL: {client.base_url} login/")
        response = await client.post('login/',data=data,headers=headers,follow_redirects=True)
    except RequestError:
        logger.error(f" Login - Cannot login as user: {kwargs['username']} pw: {kwargs['password']}")
        raise MumbleException(f"Error while loggin in with credentials\nusername: {kwargs['username']}\n{kwargs['password']}")
    t1 = datetime.now()
    d1 = t1 -t0
    logger.debug(f"Time - login (post) {d1.total_seconds()} s")
    logger.debug(f"LOGIN - Total time {(t1-t0).total_seconds()} s")
    assert_equals(response.status_code, 200,"Login failed")


async def create_ShopItem(client: AsyncClient, logger: LoggerAdapter, db: ChainDB,kwargs) -> int:
    t0 = datetime.now()
    keys = ['data_path','item_name','flag_str','logged_in','username','password']
    check_kwargs(func_name=create_ShopItem.__name__,keys=keys,kwargs=kwargs,logger=logger)
    

    try:
        logger.debug(f"REQUESTURL: {client.base_url} user_items/")
        response = await client.get('user_items/',follow_redirects=True)
    except RequestError as exc:
        raise MumbleException("Error while retrieving user items")
    t1 = datetime.now()
    d1 = t1 -t0
    logger.debug(f"Time - create_ShopItem (get user_items) {d1.total_seconds()} s")
    assert_equals(response.status_code, 200,"Getting User Items Failed!")


    try:
        logger.debug(f"REQUESTURL: {client.base_url} new_item/")
        response = await client.get('new_item/',follow_redirects=True)
    except RequestError as exc:
        raise MumbleException("Error while retrieving item creation form")
    t2 = datetime.now()
    d2 = t2 -t1
    logger.debug(f"Time - create_ShopItem (get new_item) {d2.total_seconds()} s")
    assert_equals(response.status_code, 200,"Getting Item Form Failed!")

    data_type = 'image/' + kwargs['data_path'].split('.')[1]
    data_name = kwargs['data_path'].split('/')[-1]


    data={
        'name': kwargs['item_name'],
    }

    fd, path = tempfile.mkstemp()

    with os.fdopen(fd,'wb+') as tmp:
        tmp.write(str.encode(license_from_template(kwargs['flag_str'])))
        tmp.close()
    files = [
        ('cert_license',('license.txt',open(path,'rb'),'text/plain')),
        ('data',(data_name,open(kwargs['data_path'],'rb'),data_type))
    ]
    

    headers={"Referer": f"{client.base_url}/new_item/"}   
    t3 = datetime.now()
    d3 = t3 -t2
    logger.debug(f"Time - create_ShopItem (data_processing) {d3.total_seconds()} s")
    try:
        logger.debug(f"REQUESTURL: {client.base_url} new_item/")
        response = await client.post('new_item/',data=data,files=files,headers=headers,follow_redirects=True)
    except RequestError:
        raise MumbleException("Error while submitting Shop Item")
    t4 = datetime.now()
    d4 = t4 -t3
    logger.debug(f"Time - create_ShopItem (post new_item) {d4.total_seconds()} s")
    assert_equals(response.status_code, 200, "Submitting Item Form Failed!")
    item_id = str(response.url).split("/")[4]
    logger.debug(f"CREATE-ITEM - URL: {response.url} extracted ID: {item_id} int: {int(item_id)}")
    logger.debug(f"CREATE-ITEM - Total time {(t4-t0).total_seconds()} s")
    return int(item_id)
   
    

async def create_ShopListing(client: AsyncClient, logger: LoggerAdapter, db: ChainDB,kwargs) -> int:    
    t0 = datetime.now()
    keys = ['item_id','item_price','description']
    check_kwargs(func_name=create_ShopListing.__name__,keys=keys,kwargs=kwargs,logger=logger)
    item_id = kwargs['item_id']
    try:
        logger.debug(f"REQUESTURL: {client.base_url} user_items/enlist/{item_id}/")
        response = await client.get(f'user_items/enlist/{item_id}/',follow_redirects=True)
    except RequestError:
        raise MumbleException("Error while requesting endpoint user_items")
    t1 = datetime.now()
    d1 = t1 -t0
    logger.debug(f"Time - create_ShopListing (get user_items) {d1.total_seconds()} s")

    t2 = datetime.now()
    d2 = t2 -t1
    logger.debug(f"Time - create_ShopListing (finding item_id) {d2.total_seconds()} s")
    data = {
        'price': kwargs['item_price'],
        'description': kwargs['description'],
    }
    try:
        logger.debug(f"REQUESTURL: {client.base_url} user_items/enlist/{item_id}/")
        response = await client.post(f'user_items/enlist/{item_id}/',data=data,follow_redirects=True)
    except:
        raise RequestError('Error while submitting Shop Listing!')
    t3 = datetime.now()
    d3 = t3 -t2
    logger.debug(f"CREATE_SHOPLISITING - POST STATUS_CODE: {response.status_code}")
    logger.debug(f"Time - create_ShopListing (post enlist) {d3.total_seconds()} s")
    assert_equals(response.status_code,200,"CREATE - Shop Listing Form Failed!")
    listing_id = str(response.url).split("/")[5]
    logger.debug(f"CREATE_SHOPLISTING -  created listing with ID: {listing_id} for Item with ID: {item_id}")
    return listing_id

async def create_note(client: AsyncClient, logger: Logger, db: ChainDB,kwargs) -> None:
    t0 = datetime.now()
    keys = ['note','logged_in']
    check_kwargs(func_name=create_note.__name__,keys=keys,kwargs=kwargs,logger=logger)

    try:
        logger.debug(f"REQUESTURL: {client.base_url} notes/")
        response = await client.get('notes/',follow_redirects=True)
    except RequestError:
        raise MumbleException("Error while requesting endpoint notes")    
    t1 = datetime.now()
    d1 = t1 -t0
    logger.debug(f"Time - create_note (get notes) {d1.total_seconds()} s")
    data = {
        'notes': kwargs['note'],
    }

    try:
        logger.debug(f"REQUESTURL: {client.base_url} notes/")
        response = await client.post('notes/',data=data,follow_redirects=True)
    except RequestError:
        raise MumbleException("Error while submitting notes!")
    t2 = datetime.now()
    d2 = t2 -t1
    logger.debug(f"Time - create_note (post notes) {d2.total_seconds()} s")
    logger.debug(f"CREATE LISTING - Total time {(t2-t0).total_seconds()} s")

async def logout_user(client: AsyncClient,logger: Logger, db:ChainDB, kwargs) -> None:
    keys = ['logged_in']
    check_kwargs(func_name=logout_user.__name__,keys=keys,kwargs=kwargs,logger=logger)

    try:
        logger.debug(f"REQUESTURL: {client.base_url} logout/")
        response = await client.get('logout/',follow_redirects=True)
    except RequestError as exc:
        raise MumbleException("ERROR - logging out user")
        


def exploitable_item_name(min_length:int) -> str: 

    exploitable_names = ['ss','s','i','SS','S','I']
    item_name = ''.join(secrets.choice(string.ascii_letters) for i in range(random.randint(min_length,50)))

    if any(sub in item_name for sub in exploitable_names):
        return item_name

    index = secrets.randbelow(len(item_name))
    exploit = exploitable_names[secrets.randbelow(len(exploitable_names))]
    return (item_name[:index] + exploit + item_name[index:]).upper()

async def make_item_name_exploitable(item_name:str) -> str:
    exploits = {
        'ss': 223,
        'SS': 223,
        's': 383,
        'S': 383,
        'i': 305,
        'I': 305,
    }
    res = ""
    for key in exploits:
        if key in item_name:
            index = item_name.index(key)
            res = item_name[0:index] + chr(exploits[key]) + item_name[index+len(key):]
            break
    return res