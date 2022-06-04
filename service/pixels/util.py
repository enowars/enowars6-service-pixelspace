from pixels.models import ShopItem, ShopListing
from django.contrib.auth.models import User
from django.contrib.auth.signals import user_login_failed
from django.core.exceptions import PermissionDenied, ImproperlyConfigured
from django.utils.module_loading import import_string
from django.conf import settings
import inspect
import re

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
        print(f"ITEM: {l.item.name}\nentered: {name}\nequal? {l.item.name.upper() == name.upper()}")

        if l.item.name.upper() == name.upper():

            print(f"BUYING ----> {l.item.name} now!!!")
            print(f"SHOPLISTING BUYERS STRING: {l.buyers}")
            l.buyers = user
            print(f"AFTER ADDING SHOPLISTING BUYERS STRING: {l.buyers}")              
            l.sold += 1
            l.save()
            user.profile.save()
            l.item.user.profile.save()

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