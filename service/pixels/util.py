from pixels.models import Buyers, ShopItem, ShopListing, MultiUserDict
from django.contrib.auth.models import User
from django.contrib.auth.signals import user_login_failed
from django.core.exceptions import PermissionDenied, ImproperlyConfigured
from django.utils.module_loading import import_string
from django.conf import settings
import inspect
import re
from datetime import datetime

from pixels.forms import SignupForm




def get_listings():
    return ShopListing.objects.all()

def get_listings_by_name():
    listings = ShopListing.objects.all()
    list_dict = {}
    for l in listings:
        listings[l.item.name] = l.pk
    return list_dict

def check_item_name_exists(name: str) -> bool:
    items = ShopItem.objects.all()
    for i in items:
        if i.name == name:
            return True
    return False

def update_ShopListing(id: int, user_id: int):
    listing = ShopListing.objects.get(pk=id)
   
    listing.save()

def set_buyer(user: User, name:str) -> bool:
    listings = get_listings()
    for l in listings:
        l = ShopListing.objects.get(pk=l.pk)
        if l.item.name.upper() == name.upper():            
            buyer = Buyers.objects.create(
                container=MultiUserDict.objects.get(name=f"{l.item.pk}-buyers"),
                key=str(user.username),
                value=datetime.strftime(datetime.now(), "%d/%m/%y %H:%M")
            )
            buyer.save()
            l.sold += 1
            l.save()
            
def create_user_from_form(form: SignupForm):
    user = User.objects.create(
        username= form.cleaned_data.get('username'),
        first_name= form.cleaned_data.get('first_name'),
        last_name= form.cleaned_data.get('last_name'),
        email= form.cleaned_data.get('email'),
        password= form.cleaned_data.get('password1')
    )
    print(form.cleaned_data.get('password1'))
    user.set_password(form.cleaned_data.get('password1'))
    user.save()