import os
import re
import requests
import random
import string
from typing import Optional
import tempfile

STAFF_KEY = "6DkQ5QVzCV51B086u6wb0v0hum0m1ABAIHq0fmaGtrIhR8gjkT32ASs2gjN3KoVHpZP50A47l1V274eVwxiq3mINRC21bzba7azo1K9P50rUb4r4s927MY36IsmRZxtOILTQ807LIr5BL9wtSKLI8D3p6FQXWgI1V5356WcT0Xm6vHI1mO2XrIZZsIW2mdW9DpBiVqDK3oUErwQsS0m7Zd3i45vxs5E6Ycz40gSvI2Nfg3iacSefpt4cY73vWd5BYoG8wmIU1eb5kC4KVZzuBIRR3avh4b1nty0RVW2lF6nW5Lxn64g19NUQubVqmSWhjWG957lSzr5YY5Z09Vbj555a3i7eJB60cPe0prrLpv0ew2PQ1Otfe9S0Kktu71Z7lZJW4egq0cT45h0t2pEW3NrFJ6dwc3Z2LzS0Plh8LIIONRGCmjDIInvB36bqp5QZ1t5H0aorOe9N7eB43r9lX809AUZ8oP4CP6oG4oq4VEV1OfO2W5xR"

HOST = "http://Pixelspace_service:8010/"

def get_random_string(length):
    return ''.join(random.choice(string.ascii_lowercase) for i in range(length))


class Session:
    session:requests.Session
    user:str
    password:str
    csrf_token:str

    def get_staff_key(self,): return STAFF_KEY

    def __init__(self,user="usr",password="pass",address="0.0.0.0",port="8010"):
        self.user = user
        self.password = password
        self.session = requests.Session()
        self.csrf_token = ''
        global HOST
        HOST = f"http://{address}:{port}/"
    
    def authenticate(self,):
        if self.user != "usr" or self.password != "pass":
            return self.login()
        else:
            return self.signup_new()

    def refresh_token(self,):
        if 'csrftoken' in self.session.cookies:
            self.csrf_token = self.session.cookies['csrftoken']
            return
        self.csrf_token = self.session.cookies['csrf']       

    def get_request_URL(self,URL:str,return_response:bool) -> Optional[str]:
        r = self.session.get(URL)
        self.refresh_token()
        if return_response:
            return r
    
    def create_item(self,data_path:str,item_name:str,sign_value:str) -> str:
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

        
    def login(self,) -> str:
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
    
    def signup_new(self,) -> str:
        if self.user != "usr" or self.password != "pass":
            return self.login()
        self.user = get_random_string(8)    
        self.password = "glowing4ever"
        first_name =  get_random_string(8)
        last_name = get_random_string(12)
        email = "test" + "@" + "test" +".com"
        crypt_key = STAFF_KEY

        URL = HOST + "signup/"
        self.get_request_URL(URL,return_response=False)


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
        response = self.session.post(URL,data=data,headers=headers)
        return response.status_code

    def signup(self,) -> str:
        if self.user != "usr" or self.password != "pass":
            return self.login()
        self.user = get_random_string(8)    
        self.password = get_random_string(16)

        URL = HOST + "signup/"
        self.get_request_URL(URL,return_response=False)


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

    def get_credentials(self,) -> dict:
        return {'username':self.user,'password':self.password}

    def enlist_item(self, item_name: str) -> str:
       
        item_id = self.get_item_id_by_item_name(item_name)
        
        
        self.get_request_URL(URL=HOST + f'user_items/enlist/{item_id}',return_response=True)
        
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

    def get_license(self,item_name:str) -> str:
        item_id = self.get_item_id_by_item_name(item_name)
        r = self.get_request_URL(URL=HOST + f'user_items/{item_id}',return_response=True)

        regex = '<a href="/(.+?)">View License</a>'

        return self.get_request_URL(URL=HOST + re.findall(regex,r.text)[0],return_response=True)
        


    def get_item_id_by_item_name(self,item_name:str) -> int:
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