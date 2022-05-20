import secrets
from typing import Optional
from httpx import AsyncClient
from util import Session

from enochecker3 import(
    ChainDB,
    Enochecker,
    GetflagCheckerTaskMessage,
    MumbleException,
    PutflagCheckerTaskMessage,
)

from enochecker3.utils import FlagSearcher, assert_equals, assert_in

checker = Enochecker("PixelSpaceChecker",8010)

@checker.putflag(0)
async def putflag_test(task: PutflagCheckerTaskMessage, client: AsyncClient, db: ChainDB) -> None:
    token = secrets.token_hex(32)
    item_name = 'py_req_item14'
    username = 'snuhrhlm'
    password = 'yohxzzvrtqgkqufz1'

    session = Session(user=username,password=password)
    session.login()

    r = session.create_item(data_path='/home/alex/Downloads/tests/frog.png',item_name=item_name,sign_value="ENO{TESTFLAG_STRING_VALUE}")
    assert_equals(r.status_code,200,"FLAG_STORE_1: Could not create Flagstore item!")

    r = session.enlist_item(item_name='py_req_item14')
    assert_equals(r.status_code,200,"FLAG_STORE 1: Could not enlist Flagstore item!")
    #await db.set("token",token)
    await db.set("license_flag",{'flag':token,'user':username,'password':password,'item':item_name})

@checker.getflag(0)
async def getflag_test(task: GetflagCheckerTaskMessage, client: AsyncClient, db: ChainDB) -> None:
    try:
        #token = await db.get("token")
        value_dict = await db.get("license_flag")
    except KeyError:
        raise MumbleException("Missing database entry from FLAG_STORE 1")

    session = Session(user=value_dict['user'],password=value_dict['password'])
    session.login()
    r = session.get_license(item_name=value_dict['item'])

    assert_equals(r.status_code, 200,"FLAG_STORE 1: Retrieving license flag failed!")
    assert_in(task.flag, r.text, "FLAG_STORE 1: Flag not found in license.txt!")

@checker.exploit(0)
async def exploit_test(searcher: FlagSearcher, client: AsyncClient) -> Optional[str]:
    #*
    #   Exploit_1 here
    # *#
    r = 0
    if flag:= searcher.search_flag(r.text):
        return flag

    