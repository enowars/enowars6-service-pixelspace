from django.contrib import admin
from .models import ShopItem, ShopListing

# Register your models here.
admin.site.register(ShopItem)
admin.site.register(ShopListing)