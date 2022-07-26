from pixels.models import Buyers, ShopItem,User
from datetime import datetime
from django.db import connection
from django.db.models.query import RawQuerySet



def check_item_name_exists(name: str) -> bool:

    items = ShopItem.objects.raw('SELECT * FROM pixels_shopitem WHERE lower(name) = %s',[name.lower()])    
    if len(items) == 0:
        return False
    return True
    

def set_buyer(user: User, name: str) -> bool:
    item = ShopItem.objects.raw('SELECT * FROM pixels_shopitem WHERE upper(name) = %s',[name.upper()])[0]
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
