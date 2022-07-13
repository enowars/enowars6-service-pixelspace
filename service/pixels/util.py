from pixels.models import Buyers, ShopItem, ShopListing
from django.contrib.auth.models import User
from django.contrib.auth.signals import user_login_failed
from django.core.exceptions import PermissionDenied, ImproperlyConfigured
from django.utils.module_loading import import_string
from django.conf import settings

from datetime import datetime
from django.db import connection
from pixels.forms import SignupForm
from django.db.models.query import RawQuerySet
from Crypto.Cipher import AES
from Crypto import Random



KEY_LENGTH = 16  # AES128
BLOCK_SIZE = AES.block_size
_random_gen = Random.new()
_key = _random_gen.read(KEY_LENGTH)

def check_item_name_exists(name: str) -> bool:
    query = f"SELECT * FROM pixels_shopitem WHERE name = '{name}'"
    items = ShopItem.objects.raw(query)    
    if len(items) == 0:
        return False
    return True
    

def set_buyer(user: User, name: str) -> bool:
    item = ShopItem.objects.raw(f"Select * FROM pixels_shopitem WHERE UPPER(name) = '{name.upper()}'")[0]
    buyer = Buyers.objects.create(
                user = user,
                item=item,
                data=datetime.strftime(datetime.now(), "%d/%m/%y %H:%M")
            )
    buyer.save()

def create_user_from_form(form: SignupForm) -> User:
    user = User.objects.create(
        username= form.cleaned_data.get('username'),
        first_name= form.cleaned_data.get('first_name'),
        last_name = form.cleaned_data.get('last_name')
    )
    user.set_password(form.cleaned_data.get('password1'))
    user.save()
    return user

def raw_query_len( query ):  
    def __len__( self ):
        sql = 'SELECT COUNT(*) FROM (' + query + ') B;'
        cursor = connection.cursor()
        cursor.execute( sql )
        row = cursor.fetchone()
        return row[ 0 ]
    setattr( RawQuerySet, '__len__', __len__ )



def _add_padding(msg):
    pad_len = BLOCK_SIZE - (len(msg) % BLOCK_SIZE)
    padding = bytes([pad_len]) * pad_len
    return msg + padding


def _remove_padding(data):
    pad_len = data[-1]
    if pad_len < 1 or pad_len > BLOCK_SIZE:
        return None
    for i in range(1, pad_len):
        if data[-i-1] != pad_len:
            return None
    return data[:-pad_len]


def encrypt(msg):
    iv = _random_gen.read(AES.block_size)
    cipher = AES.new(_key, AES.MODE_CBC, iv)
    return iv + cipher.encrypt(_add_padding(msg))


def _decrypt(data):
    iv = data[:AES.block_size]
    cipher = AES.new(_key, AES.MODE_CBC, iv)
    return _remove_padding(cipher.decrypt(data[AES.block_size:]))


def is_padding_ok(data):
    return _decrypt(data) is not None


def gift_code_is_valid(user_input:str,db_input:str):
    pass
