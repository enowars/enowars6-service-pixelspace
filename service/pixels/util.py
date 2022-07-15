from pixels.models import Buyers, ShopItem, ShopListing,User
from django.contrib.auth.signals import user_login_failed
from django.core.exceptions import PermissionDenied, ImproperlyConfigured
from django.utils.module_loading import import_string
from django.conf import settings

from datetime import datetime
from django.db import connection
from pixels.forms import SignupForm
from django.db.models.query import RawQuerySet


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

def raw_query_len( query ):  
    def __len__( self ):
        sql = 'SELECT COUNT(*) FROM (' + query + ') B;'
        cursor = connection.cursor()
        cursor.execute( sql )
        row = cursor.fetchone()
        return row[ 0 ]
    setattr( RawQuerySet, '__len__', __len__ )
