from django import forms
from pixels.models import ShopListing, ShopItem
from django.contrib.auth.models import User
from django.forms.widgets import HiddenInput

class ShopItemForm(forms.ModelForm):
    class Meta:
        model = ShopItem
        fields = ['name','cert_licencse','data']

class ShopListingForm(forms.ModelForm):
    class Meta:
        model = ShopListing
        fields = ['price','description','available_units']