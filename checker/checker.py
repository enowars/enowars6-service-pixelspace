import secrets
from httpx import AsyncClient
from util import *
from essential_generators import DocumentGenerator
import html
from datetime import datetime


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
        'item_price': 2147483646,
        'description': html.escape(gen.sentence()),
        'username': user['username'],
        'password': user['password1'],
    }
    logger.debug(f"ID={task.task_chain_id} PUTFLAG_LICENSE: username:{user['username']} , password: {user['password1']} , item_name: {item_name}")
    listing_id = await create_ShopListing(client=client,logger=logger,db=db,kwargs=shop_listing_kwargs)
    t4 = datetime.now()
    d3 = t4-t3
    logger.debug(f"Time - putflag_license (create_ShopListing) {d3.total_seconds()} s")
    await logout_user(client=client,logger=logger,db=db,kwargs={'logged_in':True})
    t5 = datetime.now()
    d4 = t5-t4
    logger.debug(f"Time - putflag_license (logout_user) {d4.total_seconds()} s")
    await db.set("flag", task.flag)
    await db.set("item_id", item_id)
    await db.set("user", {'user':user['username'],'password':user['password1']})
    t6 = datetime.now()
    d5 = t6-t5
    logger.debug(f"Time - putflag_license (create_ShopListing) {d5.total_seconds()} s")
    logger.debug(f"PUTFLAG_LICENSE - Total time {(t6-t1).total_seconds()} s")
    return json.dumps({'item_id':item_id})


@checker.getflag(0)
async def getflag_license(task: GetflagCheckerTaskMessage, client: AsyncClient, db: ChainDB,logger: LoggerAdapter) -> None:
    t0 = datetime.now()
    try: 
        user = await db.get("user")
    except KeyError:
        raise MumbleException("Could not retrieve USER from ChainDB!")

    try:
        flag = await db.get("flag")
    except KeyError:
        raise MumbleException("Could not retrieve FLAG from ChainDB!")
    if flag != task.flag:
        raise MumbleException(f"Flags with task_chain_id={task.task_chain_id} are different (DB and task)!")

    try:
        item_id = await db.get("item_id")
    except KeyError:
        raise MumbleException("Could not retrieve ITEM_NAME from ChainDB!")    

    login_kwargs={
        'username': user['user'],
        'password': user['password'],
    }
    await login(client=client,logger=logger,db=db,kwargs=login_kwargs)
    try:
        logger.debug(f"REQUESTURL: {client.base_url} user_items/{item_id}")
        response = await client.get(f'user_items/{item_id}',follow_redirects=True)
    except RequestError:
        raise MumbleException("Error while retrieving user items!")
    
    try:
        logger.debug(f"REQUESTURL: {client.base_url} user_items/license/{item_id}")
        response = await client.get(f"user_items/license/{item_id}",follow_redirects=True)
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
    await db.set("user", {'user':user['username'],'password':user['password1']})
    t1= datetime.now()
    logger.debug(f"PUT_NOISE_BASE - Total time {(t1-t0).total_seconds()} s")


@checker.getnoise(0)
async def get_noise_base_functions(task: GetnoiseCheckerTaskMessage, client: AsyncClient, db: ChainDB, logger: LoggerAdapter) -> None:
    t0=datetime.now()
    try: 
        user = await db.get("user")
        item_id = await db.get("item_id")
    except KeyError:
        raise MumbleException("Could not retrieve data from ChainDB!")
    
    login_kwargs={
        'username': user['user'],
        'password': user['password'],
    }

    await login(client=client,logger=logger,db=db,kwargs=login_kwargs)

    try:
        logger.debug(f"REQUESTURL: {client.base_url} user_items/{item_id}")
        response = await client.get(f'user_items/{item_id}',follow_redirects=True)
    except RequestError:
        raise MumbleException("GET_NOISE_BASE_FUNCTIONS - Error while requesting item from user_items!")
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

    
if __name__ == "__main__":
    checker.run()