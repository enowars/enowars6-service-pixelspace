from pixels.models import ShopItem, ShopListing
from django.contrib.auth.models import User

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
            l.buyers += f"-{user.pk}"
            print(f"AFTER ADDING SHOPLISTING BUYERS STRING: {l.buyers}")              
            l.sold += 1
            l.save()
            user.profile.save()
            l.item.user.profile.save()