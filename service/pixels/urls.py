from django.urls import path,include
from . import views

from django.conf import settings
from django.conf.urls.static import static
from django.contrib.staticfiles.urls import staticfiles_urlpatterns

urlpatterns = [
    #general
    path('',views.index,name='index'),
    path('signup/',views.signup,name='create_account'),
    path('login/',views.login_page,name='login'),
    path('logout/',views.logout_page,name='logout'),
    
    #shop
    path('shop/',views.shop,name='shop'),
    path('shop/<int:item_id>/',views.item,name="itemPage"),
    path('shop/purchase/<int:item_id>/',views.purchase,name="purchasePage"),

    #user
    path('user_items/',views.user_items,name='items'),
    path('user_items/<int:item_id>',views.item_page,name='itemDetails'),
    path('user_items/enlist/<int:item_id>',views.create_listing,name='listing'),
    path('user_items/review/<int:item_id>',views.review,name='review'),
    path('user_items/license/<int:item_id>',views.license_access,name='uploaded_files'),
    path('new_item/',views.create_item,name='createItem'),

    #util
    path('notes/',views.take_notes, name='notes'),
    path('giftcode/',views.gift_code, name='code'),
    #path('giftcode/create/',views.create_gift, name='createCode'),
   
]

urlpatterns += staticfiles_urlpatterns()
urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)