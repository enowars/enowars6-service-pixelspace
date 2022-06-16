from django.contrib import admin
from .models import Buyers, MultiUserDict, Receptions, ShopItem, ShopListing,Comment, Profile
# Register your models here.
admin.site.register(Profile)
admin.site.register(Comment)
admin.site.register(ShopItem)
admin.site.register(ShopListing)
admin.site.register(MultiUserDict)
admin.site.register(Buyers)
admin.site.register(Receptions)