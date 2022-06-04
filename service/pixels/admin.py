from django.contrib import admin
from .models import ShopItem, ShopListing,Comment, ForumPost, ForumTopic, Profile
# Register your models here.
admin.site.register(Profile)
admin.site.register(Comment)
admin.site.register(ShopItem)
admin.site.register(ShopListing)
admin.site.register(ForumPost)
admin.site.register(ForumTopic)
