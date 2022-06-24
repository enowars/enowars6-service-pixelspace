from pixels.models import Buyers, ShopItem, ShopListing
from django.contrib.auth.models import User
from django.contrib.auth.signals import user_login_failed
from django.core.exceptions import PermissionDenied, ImproperlyConfigured
from django.utils.module_loading import import_string
from django.conf import settings
import inspect
import re
from datetime import datetime

from pixels.forms import SignupForm

def check_item_name_exists(name: str) -> bool:
    items = ShopItem.objects.raw(f"SELECT * FROM pixels_shopitem WHERE name = '{name}'")
    if len(list(items)) == 0:
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

def create_user_from_form(form: SignupForm):
    user = User.objects.create(
        username= form.cleaned_data.get('username'),
        first_name= form.cleaned_data.get('first_name'),
        last_name= form.cleaned_data.get('last_name'),
        email= form.cleaned_data.get('email'),
        password= form.cleaned_data.get('password1')
    )
    user.set_password(form.cleaned_data.get('password1'))
    user.save()