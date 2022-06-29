import os
import re
from urllib import response
import requests
import random
import string
import tempfile
from typing import Optional, Tuple
from logging import Logger, LoggerAdapter
import secrets
import json
import hashlib
from errors import *
from files import license_from_template
from exceptions import GenericException, PixelsException
import django_random_user_hash.user as HashUser
import string_utils

 

from enochecker3 import Enochecker, PutflagCheckerTaskMessage, GetflagCheckerTaskMessage, HavocCheckerTaskMessage, ExploitCheckerTaskMessage, PutnoiseCheckerTaskMessage, GetnoiseCheckerTaskMessage, ChainDB, MumbleException, FlagSearcher
from enochecker3.utils import assert_equals, assert_in
from httpx import AsyncClient, Response, RequestError


service_port = 8010



def check_kwargs(func_name: str ,keys: list, kwargs,fileLogger: Logger): 
    for key in keys:
        if not kwargs[key]:
            fileLogger.critical(f" {func_name} - Missing KEY {key}! ")
            raise MisconfigurationError(f"FUNC: {func_name} - Kwargs has no key <{key}> !")
            return

     
async def register_user(client: AsyncClient, logger: LoggerAdapter,db: ChainDB,chain_id:int,fileLogger: Logger) -> dict:

    username = secrets.token_hex(12)
    password = secrets.token_hex(12)
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
    }

    headers={
        "Referer": f"{client.base_url}/signup/"
    }
    
    try:
        response = await client.post("signup/",data=data,headers=headers,follow_redirects=True)
    except RequestError:    
        fileLogger.error(f"Could not register USER {username} - NO RESPONSE")
        raise MumbleException(f"Error while registering user")
    
    fileLogger.info(f"Registered USER {username}")
    
    assert_equals(response.status_code, 200, "Registration failed")
    if chain_id != None:
        await db.set(chain_id+"_user",{'username':username,'password':password})
    return data


async def login(client: AsyncClient, logger: LoggerAdapter, db: ChainDB,kwargs, fileLogger: Logger) -> None:
    keys = ['username','password']
    check_kwargs(func_name=login.__name__,keys=keys,kwargs=kwargs,fileLogger=fileLogger)

    data={
        "username": kwargs['username'],
        "password": kwargs['password'],
        "next/": "shop/",
    }

    headers={
        "Referer": f"{client.base_url}/login/"
    }

    try:
        response = await client.post('login/',data=data,headers=headers,follow_redirects=True)
    except RequestError:
        fileLogger.error(f" Login - Cannot login as user: {kwargs['username']} pw: {kwargs['password']}")
        raise MumbleException(f"Error while loggin in with credentials\nusername: {kwargs['username']}\n{kwargs['password']}")
    
    assert_equals(response.status_code, 200,"Login failed")


async def create_ShopItem(client: AsyncClient, logger: LoggerAdapter, db: ChainDB,kwargs,fileLogger: Logger) -> None:
    keys = ['data_path','item_name','flag_str','logged_in','username','password']
    check_kwargs(func_name=create_ShopItem.__name__,keys=keys,kwargs=kwargs,fileLogger=fileLogger)
    await login(client=client,logger=logger,db=db,kwargs=kwargs,fileLogger=fileLogger)

    try:
        response = await client.get('user_items/',follow_redirects=True)
    except RequestError:
        #fileLogger.error(f" {__func__} - Cannot access endpoint USER_ITEMS/ as user: {kwargs['username']} (pw: {kwargs['password']}) ")
        raise MumbleException(f"Error while retrieving user items")
    
    assert_equals(response.status_code, 200,"Getting User Items Failed!")


    try:
        response = await client.get('new_item/',follow_redirects=True)
    except RequestError:
        raise MumbleException(f"Error while retrieving item creation form")
    
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

    try:
        response = await client.post('new_item/',data=data,files=files,headers=headers,follow_redirects=True)
    except RequestError:
        raise MumbleException("Error while submitting Shop Item")
    
    assert_equals(response.status_code, 200, "Submitting Item Form Failed!")
    await logout_user(client=client, logger=None,db=db,kwargs=kwargs,fileLogger=fileLogger)
    

async def create_ShopListing(client: AsyncClient, logger: LoggerAdapter, db: ChainDB,kwargs,fileLogger: Logger) -> None:    
    keys = ['item_name','item_price','description']
    check_kwargs(func_name=create_ShopListing.__name__,keys=keys,kwargs=kwargs,fileLogger=fileLogger)
    item_id = -1
    print(f"\n\n{kwargs['item_name']}\n\n")
    await login(client=client,logger=logger,db=db,kwargs=kwargs,fileLogger=fileLogger)
    regex = f'a id="self-enlist-'+kwargs['item_name']+'" href="enlist/(.+?)">Enlist item</a>'
    
    try:
        response = await client.get('user_items/',follow_redirects=True)
    except RequestError:
        raise MumbleException("Error while requesting endpoint user_items")
    print(response.text)
    match = re.findall(regex,response.text)
    item_id = match[0]

    if item_id == -1:
        raise Pixels_ShopItemError(f"Error while creating Shop Listing! Could not find ID for item with name {kwargs['item_name']}")
    else:

        data = {
            'price': kwargs['item_price'],
            'description': kwargs['description'],
            'next': 'shop/',
        }

        try:
            response = await client.post(f'user_items/enlist/{item_id}',data=data)
        except:
            raise RequestError('Error while submitting Shop Listing!')
    
        assert_equals(response.status_code,302,"CREATE - Shop Listing Form Failed!")

async def create_note(client: AsyncClient, logger: Logger, db: ChainDB,kwargs,fileLogger: Logger) -> None:
    keys = ['note','logged_in']
    check_kwargs(func_name=create_note.__name__,keys=keys,kwargs=kwargs,fileLogger=fileLogger)

    try:
        response = await client.get('notes/',follow_redirects=True)
    except RequestError:
        raise MumbleException("Error while requesting endpoint notes")    

    data = {
        'notes': kwargs['note'],
    }

    try:
        response = await client.post('notes/',data=data,follow_redirects=True)
    except RequestError:
        raise MumbleException("Error while submitting notes!")

async def logout_user(client: AsyncClient,logger: Logger, db:ChainDB, kwargs,fileLogger: Logger) -> None:
    keys = ['logged_in']
    check_kwargs(func_name=logout_user.__name__,keys=keys,kwargs=kwargs,fileLogger=fileLogger)

    try:
        response = await client.get('logout/',follow_redirects=True)
    except RequestError:
        raise MumbleException("Error while requesting endpoint logout")
        


def exploitable_item_name(min_length:int) -> str: 

    exploitable_names = ['ss','s','i','SS','S','I']
    item_name = ''.join(secrets.choice(string.ascii_letters) for i in range(random.randint(min_length,100)))

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

def adjust_pw(offset:int,pw:str) -> str:
    min = 33
    max = 126
    while offset != 0:
        if offset < max:
            max= offset
        rint = random.randint(min,max)
        if offset - rint < min:
            rint = offset
        pw += chr(rint)
        offset -= rint
    return pw


async def create_staff_user(client: AsyncClient, logger: Logger,db: ChainDB,kwargs,fileLogger: Logger) -> None:
    known_good = [
        9260, 20640, 48143, 114881, 189663, 208534, 261981, 293375, 304144, 329994, 347885,
        449225, 497661, 556423, 608984, 630902, 696892, 741704, 859564, 868048, 936481]
    keys = ['data','key','salt']
    check_kwargs(func_name=create_staff_user.__name__,keys=keys,kwargs=kwargs,fileLogger=fileLogger)
    data = kwargs['data']
    user = HashUser.User(
        f= data['first_name'],
        l= data['last_name'],
        e=data['email'],
        p1=data['password1'],
        p2=data['password2'],
        u=string_utils.shuffle(data['username']),
    )

    seed = user.gen_seed_value(salt=kwargs['salt'])
    offset = -1
    for k in known_good:
        if k-seed > 0:

            offset = k-seed
            if offset >= 0:
                break
    if offset % 2 != 0:
        alphabet = string.ascii_letters + string.digits
        for i,c in enumerate(user.username):
            if chr(ord(c)+1) in alphabet:
                user.username = '%s%s%s' %(user.username[:i],chr(ord(c)+1),user.username[i+1:])

    user.password1 = adjust_pw(offset//2,user.password1)  
    user.password2 = user.password1
    
    data={
        "username": user.username,
        "password1": user.password1,
        "password2": user.password2,
        "first_name": user.first,
        "last_name": user.last,
        "email": user.email,
        "cryptographic_key": user.gen_sha1(level=2,salt=kwargs['salt']),
        "next/": "shop/",
    }

    headers={
        "Referer": f"{client.base_url}/signup/"
    }

    try:
        response = await client.post("signup/",data=data,headers=headers,follow_redirects=True)
    except RequestError:    
        raise MumbleException(f"Error while registering user")
    
    assert_equals(response.status_code, 200, "Registration failed")
    #await db.set(kwargs['chain_id']+"_user",{'username':user.username,'password':user.password1})
    return data
    