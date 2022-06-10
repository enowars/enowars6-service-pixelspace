import secrets
from typing import Optional
from urllib.request import CacheFTPHandler
from httpx import AsyncClient
from util_old import Session
from util import *

from enochecker3 import(
    ChainDB,
    Enochecker,

    MumbleException,
    InternalErrorException,

    #FLAG-Message-Tasks
    GetflagCheckerTaskMessage,
    PutflagCheckerTaskMessage,

    #NOISE-Message-Tasks
    PutnoiseCheckerTaskMessage,
    GetnoiseCheckerTaskMessage,

    #HAVOC-Message-Tasks
    HavocCheckerTaskMessage,

    #EXPLOIT-Message-Tasks
    ExploitCheckerTaskMessage,


    
)

from enochecker3.utils import FlagSearcher, assert_equals, assert_in

checker = Enochecker("Pixelspace",8010)
def app(): return checker.app

@checker.putflag(0)
async def putflag_license(task: PutflagCheckerTaskMessage, client: AsyncClient, db: ChainDB) -> None:   
    item_name = 'CHECKER_FROG'
    username,password = await register_user(client=client,logger=None,db=db)
    shop_item_kwargs =  {
        'data_path': '/frog.png',
        'item_name': item_name,
        'logged_in': True,
        'flag_str': task.flag,
    }
    
    await create_ShopItem(client=client,logger=None,db=db,kwargs=shop_item_kwargs)
    shop_listing_kwargs = {
        'item_name': item_name,
        'item_price': 100.0,
        'description': 'THIS IS SUPER EXPENSIVE GG CHECKER',
    }
    await create_ShopListing(client=client,logger=None,db=db,kwargs=shop_listing_kwargs)
    await logout_user(client=client,logger=None,db=db,kwargs={'logged_in':True})
    await db.set("license_flag",{'flag':task.flag,'user':username,'password':password,'item':item_name})


@checker.getflag(0)
async def getflag_license(task: GetflagCheckerTaskMessage, client: AsyncClient, db: ChainDB) -> None:
    item_id = -1
    regex_item = '<a href="(.+?)">View Item</a>'
    regex_license = '<a href="/(.+?)">View License</a>'

    try: 
        object = await db.get("license_flag")
    except DBSearchError:
        raise MumbleException("Could not retrieve data from ChainDB!")

    login_kwargs={
        'username': object['user'],
        'password': object['password'],
    }
    await login(client=client,logger=None,db=db,kwargs=login_kwargs)
    try:
        response = await client.get('user_items/',follow_redirects=True)
    except RequestError:
        raise MumbleException("Error while retrieving user items!")
    
    
    item_id = re.findall(regex_item,response.text)[0]
    if item_id == -1:
        raise MumbleException("Errow while searching for flag item (license)!")

    try:  
        response = await client.get(f'user_items/{item_id}',follow_redirects=True)
    except RequestError:
        raise MumbleException(f"Error while viewing user item with id: {item_id}")
    
    license_url = re.findall(regex_license,response.text)[0]

    try:
        response = await client.get(f"{license_url}",follow_redirects=True)
    except RequestError:
        raise MumbleException(f"Error while viewing license of user item with id: {item_id}")
        
    assert_in(object['flag'],response.text)    
    


@checker.putflag(1)
async def putflag_notes(task: PutflagCheckerTaskMessage, client: AsyncClient, db: ChainDB) -> None:    
    username,password = await register_user(client=client,logger=None,db=db)
    note_kwargs = {
        'note':task.flag,
        'logged_in': True,
    }
    await create_note(client=client,logger=None,db=db,kwargs=note_kwargs)
    await db.set('note_flag',{'flag':task.flag,'user':username,'password':password})

@checker.getflag(1)
async def getflag_notes(task: GetflagCheckerTaskMessage, client: AsyncClient, db: ChainDB) -> None:
    regex_notes = '<input type="text" name="notes" value="(.+?)" maxlength="50000" required id="id_notes">'
    try: 
        object = await db.get("note_flag")
    except DBSearchError:
        raise MumbleException("Could not retrieve data from ChainDB!")

    login_kwargs={
        'username': object['user'],
        'password': object['password'],
    }
    await login(client=client,logger=None,db=db,kwargs=login_kwargs)
    try:
        response = await client.get('notes/',follow_redirects=True)
    except RequestError:
        raise MumbleException("Error while retrieving user items!")

    match = re.findall(regex_notes,response.text)[0]
    assert_in(object['flag'],match)
"""
@checker.havoc(0)
async def havoc(task: HavocCheckerTaskMessage, client: AsyncClient, db: ChainDB) -> None:
    endpoints = [
        'signup',
        'login',
        'logout',
        'shop',
        #'shop/1',
        #'shop/purchase/1',
        'user_items/',
        #'user_items/1',
        #'user_items/enlist/1',
        #'user_items/review/1',
        'new_item/',
        'debug_env',
    ]
    session = Session(address=task.address,port=8010)
    for point in endpoints:
        URL = session.get_base_URL() + point + "/"
        res = await session.get_request_URL(URL,return_response=True)
        if res.status_code == 404:
            raise MumbleException(f'HAVOC - Endpoint "{point}" not reachable')
        
"""

@checker.putnoise(0)
async def put_noise(task: PutnoiseCheckerTaskMessage, client: AsyncClient, db: ChainDB) -> None:
    await register_user(client,None)

@checker.getnoise(0)
async def get_noise(task: GetnoiseCheckerTaskMessage, client: AsyncClient, db: ChainDB) -> None:
    print("GET_NOISE")

if __name__ == "__main__":
    checker.run()
