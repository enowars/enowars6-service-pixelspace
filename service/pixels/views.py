from django.shortcuts import render,redirect
from django.http import HttpResponse,HttpResponseRedirect
from django.urls import reverse
from django.http.response import FileResponse
# Create your views here.
from django.contrib.auth import get_user_model
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.decorators import user_passes_test
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth.models import Permission
from pixels.models import *
from pixels.forms import *
from pixels.util import *
from django.conf import settings
import django_random_user_hash.user as HashUser
from django.contrib import messages
from django.db import transaction
from django.urls import reverse

from datetime import timedelta
from django.utils import timezone
import re
from django.db import connection
from django.db import connections
"""
permissionsModels = ['_shopitem','_shoplisting']
permissionsOptions = ['add','change','delete','view']
            

PERMISSIONS = Permission.objects.get()
"""

def debug(request):
    #print(str(connection.queries))
    return HttpResponse("connection="+repr(connection.queries) + "\nconnections=" + repr(connections))




def logout_page(request):
    if request.user is not None:
        logout(request)
    return redirect('../')


def login_page(request):
    if request.user.is_authenticated:
        return redirect('items')
    if request.method == 'GET':
        form = AuthenticationForm()
        return render(request, 'login.html', {'form': form})
    if request.method == 'POST':
        form = AuthenticationForm(request=request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)
            if user is not None:
                login(request, user)
                return redirect('items')
        else:
            # If there were errors, we render the form with these
            # errors
            return render(request, 'login.html', {'form': form}) 
   
    return render(request,'login.html',{'form':form})

def index(request):
    return render(request,'index.html')

def signup(request):
    if request.method == 'POST':
        form = SignupForm(request.POST)
        
        if form.is_valid():      
            user = create_user_from_form(form)            
            user.profile.first_name = user.first_name
            user.profile.last_name = user.last_name
            user.profile.expiration_date = timezone.now() + timedelta(minutes=11)
            
            for i in range(29,37):
                user.user_permissions.add(i)
            
            user.profile.save()
            user.save()
            login(request, user)
            #print(f"Registered USER {user.username}")
            return redirect('items')
        else:
            errors = "ERROR 406 - Not Acceptable\n" + form.errors.as_text()
            messages.error(request,errors)
            return render(request, 'signup.html', {'form': form},status=406)
    else:
        form = SignupForm()
    return render(request, 'signup.html', {'form': form})

def shop(request,page_num):
    prev_page = page_num -1
    next_page = page_num +1

    if page_num == 0:
        prev_page = None

    query = f"SELECT * FROM pixels_shoplisting ORDER BY id ASC OFFSET {(page_num -1) *5} ROW FETCH NEXT 5 ROWS ONLY"
    items = ShopListing.objects.raw(query)

    if len(items) < 5:
        next_page = None

    return render(request,'shop.html',{'shop_items':items,'prev': prev_page, 'next':next_page, 'current': page_num})

def item(request,item_id):
    avg_rating = 0
    content_dict = {}
    content_dict['item'] = ShopListing.objects.get(pk=item_id)
    
    query = f"SELECT * FROM pixels_comment WHERE item_id = {item_id}"
    content_dict['reviews'] = Comment.objects.raw(query)
    num_revs = len(content_dict['reviews'])
    for r in content_dict['reviews']:
        avg_rating += r.stars
    if num_revs != 0:
        avg_rating /= num_revs
    content_dict['rating'] = avg_rating
    return render(request, 'shop_item.html', content_dict)

@transaction.atomic
def db_create_item(form: ShopItemForm,user:User):
    obj = form.save(commit=False)
    obj.user = user
    obj.cert_licencse = form.cleaned_data.get('cert_licencse')
    obj.data = form.cleaned_data.get('data')
    obj.save()  
    return obj.pk,obj.name

def create_item(request):
    if request.method == 'POST':
        form = ShopItemForm(request.POST,request.FILES,request.user)
        if form.is_valid():                  
            if check_item_name_exists(form.cleaned_data.get('name')):
                messages.error(request,'An item with this name already exists! Please choose another one!')
                return redirect('createItem')    
            item_id, item_name = db_create_item(form=form,user=request.user)
            #print(f"CREATED ITEM with id: {item_id}")  
            messages.success(request,f"Successfully created item with id: {item_id}")
            return redirect(f"../user_items/{item_id}")
    else:
        form = ShopItemForm()
    return render(request, 'new_item.html',{'form':form})

def user_items(request):
    content_dict = {}
    content_dict['user_items'] = ShopItem.objects.filter(user=request.user)
    content_dict['user_listings'] = ShopListing.objects.filter(item__user=request.user)
    content_dict['user_bought'] = Buyers.objects.filter(user=request.user)

    return render(request,'user_items.html',content_dict)

@transaction.atomic
def db_create_listing(form: ShopListingForm,item_id):
    obj = form.save(commit=False)
    obj.item = ShopItem.objects.get(pk=item_id)
    obj.description = form.cleaned_data.get('description')
    obj.sold = 0
    obj.save()
    return obj.pk,obj.item.name

def create_listing(request,item_id):
    if request.method == 'POST':
        form = ShopListingForm(request.POST,request.FILES,request.user)
        if form.is_valid():
            listing_id,item_name = db_create_listing(form,item_id)
            #print(f"CREATED LISTING for item: {listing_id}")
            messages.success(request,f"Successfully created listing with id: {listing_id}")
            return redirect("itemPage",item_id=listing_id)
    else:
        form = ShopListingForm()
    return render(request, 'enlist_item.html', {'form': form,'user_item':ShopItem.objects.get(pk=item_id)})

@transaction.atomic
def purchase(request,item_id):
    item = ShopListing.objects.select_for_update().raw(f"SELECT * FROM pixels_shoplisting WHERE id = {item_id}")[0]
    buyer = request.user
    query = f"SELECT * FROM pixels_buyers WHERE user_id = {buyer.pk} AND item_id = {item_id}"
    buyers = Buyers.objects.raw(query)
    if len(buyers) > 0:
        messages.error(request,'You already purchased this item!')
        return redirect('items')

    if request.user == item.item.user:
        messages.error(request,'You cannot buy your own item!')
        return redirect('shop',page_num=1)
    if buyer.profile.balance >= item.price:
        item.item.user.profile.balance += item.price
        item.item.user.profile.save()
        buyer.profile.balance -= item.price
        buyer.profile.save()
        set_buyer(buyer,item.item.name)
        item.sold +=1
        #print(f"USER: {request.user} bought item: {item.item.name}")
        messages.success(request,f"Successfully bought item: {item.item.name} ({item.item.pk})")
        item.save()
    else:
        messages.error(request,'You cannot aford to buy this item!')
        return redirect('items')
    return redirect('items')
    

def item_page(request,item_id):
    return render(request, 'item_details.html', {'item': ShopItem.objects.get(id=item_id)})


def review(request,item_id):
    if request.method == 'POST':
        form = CommentForm(request.POST)
        if form.is_valid():
            com = form.save(commit=False)
            reception = Comment.objects.create(
                item = ShopListing.objects.raw(f"SELECT * FROM pixels_shoplisting WHERE item_id = {item_id}")[0],
                user = request.user,
                content =  com.content,
                stars = com.stars,
                date = datetime.strftime(datetime.now(), "%d/%m/%y %H:%M")
            )
            reception.save()
            return redirect('items')
    else:
        form = CommentForm()
    return render(request,'review.html',{'form': form})



def take_notes(request):
    if request.method == 'POST':
        form = NoteForm(request.POST)
        if form.is_valid():
            notes = form.cleaned_data.get('notes')
            with connection.cursor() as cursor:
                cursor.execute("UPDATE pixels_profile SET notes = %s WHERE user_id = %s",[notes,request.user.id])            
            return redirect('items')
    else:
        form = NoteForm(initial={'notes':request.user.profile.notes})
    return render(request, 'notes.html', {'form': form})
    

def gift_code(request):
    if request.method == 'POST':
        form = GiftReceiveForm(request.POST,request.USER)
        query = f"SELECT * FROM pixels_gift WHERE code = {form.cleaned_data.get('code')}"
        codes = Gift.objects.raw(query)
        if len(codes) == 0:
            messages.error(request,"Entered giftcode is invalid!")
            return render(request, 'giftcode_create.html', {'form': form})
        else:
            obj = form.save(commit=False)
    else:
        form = GiftReceiveForm()
    return render(request, 'giftcode.html', {'form': form})

def create_gift(request):
    if request.method == 'POST':
        form = GiftCreationForm(request.POST)
        if form.is_valid():
         
            item_id = int(re.findall("\((.+?)\)",str(form.cleaned_data.get('item')))[0])
            #print(f"\n\n\n\n\n{item_id,type(item_id)}\n\n\n\n\n")
            item = ShopItem.objects.raw(f"Select * FROM pixels_shopitem WHERE id = {item_id}")[0]
            obj = Gift.objects.create(
                code = form.cleaned_data.get("code"),
                item = item,
                users = Buyers.objects.create(
                    user = request.user,
                    item = item,
                    data = datetime.strftime(datetime.now(), "%d/%m/%y %H:%M")
                )
            )
            obj.save()
            messages.success(request,"Successfully created giftcode!")
            return render(request, 'giftcode_create.html', {'form': form,'user_id': request.user.id})
       
        messages.error(request,form.errors)
        messages.error(request,item_id)
        return render(request, 'giftcode_create.html', {'form': form,'user_id': request.user.id})
    else:
        form = GiftCreationForm({'request':request},initial={'code':"TEST_CODE"})
        form.fields['item'].queryset = ShopItem.objects.filter(user_id = request.user.id)
    return render(request, 'giftcode_create.html', {'form': form,'user_id': request.user.id})

def gift_item_via_code(request,code_id):
    gift_item = Gift.objects.get(pk=code_id)
    if request.method == 'POST':
        form = GiftReceiveForm(request.POST)
        if form.is_valid():
            if gift_code_is_valid(form.cleaned_data.get("code"),gift_item.code):
                obj = Buyers.objects.create(
                    user = request.user,
                    item= gift_item.item,
                    data=datetime.strftime(datetime.now(), "%d/%m/%y %H:%M")
                ) 
                obj.save()
            else:
                messages.error("Invalid Item-Code")
            return redirect('itemDetails', code_id=gift_item.item.id)
            
            
    
    return render(request,'giftcode_item.html',{'form':form,'item':gift_item})

def license_access(request, item_id):    
    access_granted = False
    user = request.user
    item = ShopItem.objects.get(pk=item_id)
    if user.is_authenticated:
        if user == item.user:
            response = FileResponse(item.cert_license)
            return response
        query = f"SELECT * FROM pixels_buyers WHERE item_id = {item.pk} AND user_id = {user.pk}"
        buyers = Buyers.objects.raw(query)
        if len(buyers) > 0:
            access_granted = True  
    if access_granted:
        response = FileResponse(item.cert_license)
        return response
    else:
        messages.error(request,'You are not allowed to view this content!')
        return redirect('items')
    
