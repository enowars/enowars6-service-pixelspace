import secrets
from typing import Optional
from httpx import AsyncClient
from util import Session

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

checker = Enochecker("PixelSpace",8010)
def app(): return checker.app

@checker.putflag(0)
async def putflag_test(task: PutflagCheckerTaskMessage, client: AsyncClient, db: ChainDB) -> None:    
    item_name = 'py_req_item15'
    username = 'snuhrhlm'
    password = 'yohxzzvrtqgkqufz1'

    session = Session(user=username,password=password,address=task.address,port=8010)
    session.authenticate()

    r = session.create_item(data_path='frog.png',item_name=item_name,sign_value=f"ENO{task.flag}")
    print(f"\n Create item response: {r.status_code}\n")
    assert_equals(r.status_code,200,"FLAG_STORE_1: Could not create Flagstore item!")

    r = session.enlist_item(item_name='py_req_item14')
    assert_equals(r.status_code,200,"FLAG_STORE 1: Could not enlist Flagstore item!")
    
    await db.set("license_flag",{'flag':task.flag,'user':username,'password':password,'item':item_name})

@checker.getflag(0)
async def getflag_test(task: GetflagCheckerTaskMessage, client: AsyncClient, db: ChainDB) -> None:
    try:
        #token = await db.get("token")
        value_dict = await db.get("license_flag")
    except KeyError:
        raise MumbleException("Missing database entry from FLAG_STORE 1")

    session = Session(user=value_dict['user'],password=value_dict['password'],address=task.address,port=8010)
    session.login()
    r = session.get_license(item_name=value_dict['item'])

    assert_equals(r.status_code, 200,"FLAG_STORE 1: Retrieving license flag failed!")
    assert_in(task.flag, r.text, "FLAG_STORE 1: Flag not found in license.txt!")


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
        
    
if __name__ == "__main__":
    checker.run()
