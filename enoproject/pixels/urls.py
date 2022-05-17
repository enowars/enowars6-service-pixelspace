from django.urls import path,include
from . import views



from django.conf import settings
from django.conf.urls.static import static


urlpatterns = [
    path('',views.index,name='index'),
    path('signup/',views.signup,name='create_account'),
    path('login/',views.login_page,name='login'),
    path('logout/',views.logout_page,name='logout'),
    path('seed/',views.server_seed, name='serv_seed'),

    path('shop/',views.shop,name='shop'),
    path('shop/<int:item_id>/',views.item,name="itemPage"),
    path('shop/purchase/<int:item_id>/',views.purchase,name="purchasePage"),

    path('user_items/',views.user_items,name='items-'),
    path('user_items/enlist/<int:item_id>',views.create_listing,name='listing'),
    path('new_item/',views.create_item,name='createItem'),
    
    
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)