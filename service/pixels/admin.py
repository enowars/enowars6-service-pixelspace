from django.contrib import admin
from .models import Buyers, ShopItem, ShopListing,Comment, Profile

admin.site.register(Profile)
admin.site.register(Comment)
admin.site.register(ShopItem)
admin.site.register(ShopListing)
admin.site.register(Buyers)
