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



def check_kwargs(func_name: str ,keys: list, kwargs): 
    for key in keys:
        if not kwargs[key]:
            raise MisconfigurationError(f"FUNC: {func_name} - Kwargs has no key <{key}> !")
            return

async def refresh_token(client: AsyncClient, url: str) -> str:
    token =""
    try:
        response = await client.get(url,follow_redirects=True)
        try:            
            token = response.cookies['csrftoken']    
        except CSRFRefreshError:
            raise MumbleException(f"Error while requesting new token from {url} - No cookie value!")
    except RequestError:
        raise MumbleException(f"Error while requesting new token from {url} - Response failed!")
    return token
        
        
    


async def register_user(client: AsyncClient, logger: LoggerAdapter,db: ChainDB,chain_id:int) -> Tuple[str,str]:

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

    headers={
        "Referer": f"{client.base_url}/signup/"
    }

    try:
        response = await client.post("signup/",data=data,headers=headers,follow_redirects=True)
    except RequestError:    
        raise MumbleException(f"Error while registering user")
    
    assert_equals(response.status_code, 200, "Registration failed")
    if chain_id != None:
        await db.set(chain_id+"_user",{'username':username,'password':password})
    return data


async def login(client: AsyncClient, logger: LoggerAdapter, db: ChainDB,kwargs) -> None:
    keys = ['username','password']
    check_kwargs(func_name=login.__name__,keys=keys,kwargs=kwargs)

    data={
        "username": kwargs['username'],
        "password": kwargs['password'],
        "next/": "shop/",
        "csrfmiddlewaretoken": await refresh_token(client,"login/")
    }

    headers={
        "Referer": f"{client.base_url}/login/"
    }

    try:
        response = await client.post('login/',data=data,headers=headers,follow_redirects=True)
    except RequestError:
        raise MumbleException(f"Error while loggin in with credentials\nusername: {kwargs['username']}\n{kwargs['password']}")
    
    assert_equals(response.status_code, 200,"Login failed")


async def create_ShopItem(client: AsyncClient, logger: LoggerAdapter, db: ChainDB,kwargs) -> None:
    keys = ['data_path','item_name','flag_str','logged_in']
    check_kwargs(func_name=create_ShopItem.__name__,keys=keys,kwargs=kwargs)

    if kwargs['logged_in'] == False:
        await login(client=client,logger=logger,db=db)
        data={"csrfmiddlewaretoken": await refresh_token(client,"shop/")}
        headers={"Referer": f"{client.base_url}/shop/"}    

        try:
            response = await client.get('user_item/',follow_redirects=True)
        except RequestError:
            raise MumbleException(f"Error while retrieving user items")
        
        assert_equals(response.status_code, 200,"Getting User Items Failed!")


    data={"csrfmiddlewaretoken": await refresh_token(client,"user_items/")}
    headers={"Referer": f"{client.base_url}/user_items/"}   

    try:
        response = await client.get('new_item/',follow_redirects=True)
    except RequestError:
        raise MumbleException(f"Error while retrieving item creation form")
    
    assert_equals(response.status_code, 200,"Getting Item Form Failed!")

    data_type = 'image/' + kwargs['data_path'].split('.')[1]
    data_name = kwargs['data_path'].split('/')[-1]


    data={
        'csrfmiddlewaretoken': await refresh_token(client,"new_item/"),
        'name': kwargs['item_name'],
        'data_name': data_name,
    }

    fd, path = tempfile.mkstemp()

    with os.fdopen(fd,'wb+') as tmp:
            tmp.write(str.encode(license_from_template(kwargs['flag_str'])))
            tmp.close()
    files = [
        ('cert_licencse',('license.txt',open(path,'rb'),'text/plain')),
        ('data',(data_name,open(kwargs['data_path'],'rb'),data_type))
    ]

    headers={"Referer": f"{client.base_url}/new_item/"}   

    try:
        response = await client.post('new_item/',data=data,files=files,headers=headers)
    except RequestError:
        raise MumbleException("Error while submitting Shop Item")
    
    assert_equals(response.status_code, 302, "Submitting Item Form Failed!")


async def create_ShopListing(client: AsyncClient, logger: LoggerAdapter, db: ChainDB,kwargs) -> None:    
    keys = ['item_name','item_price','description']
    check_kwargs(func_name=create_ShopListing.__name__,keys=keys,kwargs=kwargs)

    item_id = -1
    regex1 = '<td>(.+?)</td>'
    regex2 = '<a href="enlist/(.+?)">'

    try:
        response = await client.get('user_items/',follow_redirects=True)
    except RequestError:
        raise MumbleException("Error while requesting endpoint user_items")

    match = re.findall(regex1,response.text)
    
    for i in range(0,len(match),3):
        if match[i] == kwargs['item_name']:
            item_id = int(re.findall(regex2,match[i+1])[0])

    if item_id == -1:
        raise Pixels_ShopItemError(f"Error while creating Shop Listing! Could not find ID for item with name {kwargs['item_name']}")
    else:

        data = {
            'price': kwargs['item_price'],
            'description': kwargs['description'],
            'csrfmiddlewaretoken': await refresh_token(client,f'user_items/enlist/{item_id}'),
            'next': 'shop/',
        }

        try:
            response = await client.post(f'user_items/enlist/{item_id}',data=data)
        except:
            raise RequestError('Error while submitting Shop Listing!')
    
        assert_equals(response.status_code,302,"CREATE - Shop Listing Form Failed!")

async def create_note(client: AsyncClient, logger: LoggerAdapter, db: ChainDB,kwargs) -> None:
    keys = ['note','logged_in']
    check_kwargs(func_name=create_note.__name__,keys=keys,kwargs=kwargs)

    try:
        response = await client.get('notes/',follow_redirects=True)
    except RequestError:
        raise MumbleException("Error while requesting endpoint notes")    

    data = {
        'notes': kwargs['note'],
        'csrfmiddlewaretoken': await refresh_token(client,"notes/"),
    }

    try:
        response = await client.post('notes/',data=data,follow_redirects=True)
    except RequestError:
        raise MumbleException("Error while submitting notes!")

async def logout_user(client: AsyncClient,logger: LoggerAdapter, db:ChainDB, kwargs) -> None:
    keys = ['logged_in']
    check_kwargs(func_name=logout_user.__name__,keys=keys,kwargs=kwargs)

    try:
        response = await client.get('logout/',follow_redirects=True)
    except RequestError:
        raise MumbleException("Error while requesting endpoint logout")


def exploitable_item_name(min_length:int) -> str: 

    exploitable_names = ['ss','s','i','SS','S','I']
    item_name = ''.join(secrets.choice(string.ascii_letters) for i in range(random.randint(min_length,18)))

    if any(sub in item_name for sub in exploitable_names):
       return item_name

    index = secrets.randbelow(len(item_name))
    exploit = exploitable_names[secrets.randbelow(len(exploitable_names))]
    return item_name[:index] + exploit + item_name[index:]

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


async def create_staff_user(client: AsyncClient, logger: LoggerAdapter,db: ChainDB,kwargs) -> None:
    known_good = [
        9260, 20640, 48143, 114881, 189663, 208534, 261981, 293375, 304144, 329994, 347885,
        449225, 497661, 556423, 608984, 630902, 696892, 741704, 859564, 868048, 936481]
    keys = ['data','key','salt','chain_id']
    check_kwargs(func_name=create_staff_user.__name__,keys=keys,kwargs=kwargs)
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
        "csrfmiddlewaretoken": await refresh_token(client,"signup/")
    }

    headers={
        "Referer": f"{client.base_url}/signup/"
    }

    try:
        response = await client.post("signup/",data=data,headers=headers,follow_redirects=True)
    except RequestError:    
        raise MumbleException(f"Error while registering user")
    
    assert_equals(response.status_code, 200, "Registration failed")
    await db.set(kwargs['chain_id']+"_user",{'username':user.username,'password':user.password1})
    return data
    