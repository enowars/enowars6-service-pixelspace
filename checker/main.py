import sys
import requests
import random
import string

def get_csrf_token(cli_session) -> str:
    if 'csrftoken' in cli_session.cookies:
        return cli_session.cookies['csrftoken']
    return cli_session.cookies['csrf']

def get_random_string(length):
    return ''.join(random.choice(string.ascii_lowercase) for i in range(length))


def get_username_option(string: str) -> int:
    return 1

def login(username: str, password:str):
    URL = 'http://0.0.0.0:8010/login/'

    client = requests.session()

    # Retrieve the CSRF token first
    client.get(URL)  # sets cookie
    csrftoken = get_csrf_token(client)

    login_data = dict(username=username, password=password, csrfmiddlewaretoken=csrftoken, next='shop/')
    r = client.post(URL, data=login_data, headers=dict(Referer=URL))
    print(f"LOGIN: <POST> {r.status_code}" )

    r_i = client.get('http://0.0.0.0:8010/user_items/')
    csrftoken = get_csrf_token(client)
    print(f"USER_ITEMS: <GET> {r_i.status_code}")

    r_i = client.get('http://0.0.0.0:8010/new_item/')
    csrftoken = get_csrf_token(client)
    print(f"CREATE_ITEM: <GET> {r_i.status_code}" )
   
   
    files = {'data':open('/home/alex/Downloads/tests/frog.png','rb'),'cert_licencse':open('/home/alex/Downloads/tests/license.txt','rb')}
    create_item_headers = dict(name="python_request_item", data=files['data'],cert_licencse=files['cert_licencse'],csrfmiddlewaretoken=csrftoken)

    r_i = client.post("http://0.0.0.0:8010/new_item/",data=create_item_headers,files=files)

    print(f"CREATE_ITEM: <POST> {r_i.status_code}" )
    if r_i.status_code not in [200,201]:
        print(r_i.text)




def signup() ->  dict:
    username = get_random_string(8)
    password = get_random_string(16) + "1"

    URL = 'http://0.0.0.0:8010/signup/'

    client = requests.session()

    client.get(URL)  # sets cookie
  
    csrftoken = get_csrf_token(client)

    login_data = dict(username=username, password1=password,password2=password, csrfmiddlewaretoken=csrftoken, next='shop/')
    r = client.post(URL, data=login_data, headers=dict(Referer=URL))
    print(r.status_code)
    return [username,password]

credentials = signup()
print(credentials)
login(username=credentials[0],password=credentials[1])

