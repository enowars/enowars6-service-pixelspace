import os
import re
import requests
import random
import string
import tempfile
from typing import Optional, Tuple
from logging import LoggerAdapter
import secrets
import json
 

from enochecker3 import Enochecker, PutflagCheckerTaskMessage, GetflagCheckerTaskMessage, HavocCheckerTaskMessage, ExploitCheckerTaskMessage, PutnoiseCheckerTaskMessage, GetnoiseCheckerTaskMessage, ChainDB, MumbleException, FlagSearcher
from enochecker3.utils import assert_equals, assert_in
from httpx import AsyncClient, Response, RequestError



HOST = "http://Pixelspace_service:8010/"

def get_random_string(length):
    return ''.join(random.choice(string.ascii_lowercase) for i in range(length))


class Session:
    session:requests.Session
    user:str
    password:str
    csrf_token:str
    host_ip:str
    host_port:str


    def __init__(self,user="usr",password="pass",address="0.0.0.0",port="8010"):
        self.user = user
        self.password = password
        self.session = requests.Session()
        self.csrf_token = ''
        self.host_ip = address
        self.host_port = port
        global HOST
        HOST = f"http://{address}:{port}/"
    
    async def authenticate(self,):
        if self.user != "usr" or self.password != "pass":
            return self.login()
        else:
            return self.signup_new()

    async def refresh_token(self,):
        if 'csrftoken' in self.session.cookies:
            self.csrf_token = self.session.cookies['csrftoken']
            return
        self.csrf_token = self.session.cookies['csrf']       

    async def get_request_URL(self,URL:str,return_response:bool) -> Optional[str]:
        r = self.session.get(URL)
        await self.refresh_token()
        if return_response:
            return r

    def get_base_URL(self,) -> str:
        return "http://" + self.host_ip + ":" + self.host_port + "/"
    
    async def create_item(self,data_path:str,item_name:str,sign_value:str) -> str:
        URL = HOST + 'new_item/'
        self.get_request_URL(URL=HOST + 'user_items/',return_response=False)
        self.get_request_URL(URL=HOST + 'new_item/',return_response=False)
        

        data_type = 'image/' + data_path.split('.')[1]
        data_name = data_path.split('/')[-1]
        response = 0
        data = {
            'csrfmiddlewaretoken': self.csrf_token,
            'name': item_name,
            }
        
        fd, path = tempfile.mkstemp()
       
        with os.fdopen(fd,'wb+') as tmp:
            tmp.write(str.encode(self.license_from_template(sign_value)))
            tmp.close()
        files = [
            ('cert_licencse',('license.txt',open(path,'rb'),'text/plain')),
            ('data',(data_name,open(data_path,'rb'),data_type))
        ]

        return self.session.post(url=URL,data=data,files=files)

        
    async def login(self,) -> str:
        if self.user == "usr" or self.password == "pass":
            print("DEFAULT USER OR PASSWORD STILL SET. THIS IS NOT VALID")
            exit(1)
        URL = HOST + 'login/'
        self.get_request_URL(URL=URL,return_response=False)

        data = {
            'username': self.user,
            'password': self.password,
            'csrfmiddlewaretoken': self.csrf_token,
            'next': 'shop/'
        }
        
        headers = {
            'Referer': URL
        }

        response = self.session.post(URL,data=data,headers=headers)
        return response
    
    async def signup_new(self,) -> str:
        if self.user != "usr" or self.password != "pass":
            return self.login()
        self.user = get_random_string(8)    
        self.password = "glowing4ever"
        first_name =  get_random_string(8)
        last_name = get_random_string(12)
        email = "test" + "@" + "test" +".com"
        crypt_key = STAFF_KEY

        URL = HOST + "signup/"
        await self.get_request_URL(URL,return_response=False)


        data = { 
            'username': self.user,
            'password1': self.password,
            'password2': self.password,
            'first_name': first_name,
            'last_name': last_name,
            'email': email,
            'cryptographic_key': crypt_key,
            'csrfmiddlewaretoken': self.csrf_token,
            'next': 'shop/'
        }
        
        headers = {
            'Referer': URL
        }

        print(f"USERNAME: {self.user}")
        print(f"PASSWORD: {self.password}")
        response = await self.session.post(URL,data=data,headers=headers)
        return response.status_code

    async def signup(self,) -> str:
        if self.user != "usr" or self.password != "pass":
            return self.login()
        self.user = get_random_string(8)    
        self.password = get_random_string(16)

        URL = HOST + "signup/"
        await self.get_request_URL(URL,return_response=False)


        data = {
            'username': self.user,
            'password1': self.password,
            'password2': self.password,
            'csrfmiddlewaretoken': self.csrf_token,
            'next': 'shop/'
        }
        
        headers = {
            'Referer': URL
        }

        response = self.session.post(URL,data=data,headers=headers)
        return response.status_code

    async def get_credentials(self,) -> dict:
        return {'username':self.user,'password':self.password}

    async def enlist_item(self, item_name: str) -> str:
       
        item_id = self.get_item_id_by_item_name(item_name)
        
        
        await self.get_request_URL(URL=HOST + f'user_items/enlist/{item_id}',return_response=True)
        
        form_data = {
            'price': 1.0,
            'description':'This may be some aweful description.',
            'csrfmiddlewaretoken':self.csrf_token,
            'next':'shop/'
            }
        
        return self.session.post(url=HOST + f'user_items/enlist/{item_id}',data=form_data)
    
        
    def license_from_template(self, sign_value: str) -> str:
        return f"""
        Copyright 2022 NOBODY

        Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"),
        to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense,
        and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:

        The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.
        THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
        FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
        LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER
        DEALINGS IN THE SOFTWARE.

        Well this is a fake :(

        Greetings from the Enowars-Team
        {sign_value}
        """

    async def get_license(self,item_name:str) -> str:
        item_id = self.get_item_id_by_item_name(item_name)
        r = self.get_request_URL(URL=HOST + f'user_items/{item_id}',return_response=True)

        regex = '<a href="/(.+?)">View License</a>'

        return self.get_request_URL(URL=HOST + re.findall(regex,r.text)[0],return_response=True)
        


    async def get_item_id_by_item_name(self,item_name:str) -> int:
        item_id = -1
        r = self.get_request_URL(URL=HOST + 'user_items/',return_response=True)

        regex1 = '<td>(.+?)</td>'
        regex2 = '<a href="enlist/(.+?)">'
        match = re.findall(regex1,r.text)

        for i in range(0,len(match),3):
            if match[i] == item_name:
                item_id = int(re.findall(regex2,match[i+1])[0])

        if item_id == -1:
            #put some senceful exception here
            print("ITEM WAS EITHER NOT SUBMITTED BY THIS USER OR GOT DELETED!")
            exit(0)
        return item_id

    