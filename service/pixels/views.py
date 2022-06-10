from django.shortcuts import render,redirect
from django.http import HttpResponse,HttpResponseRedirect
from django.urls import reverse
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
import hashlib
import random
import string
import os

def group_required(*group_names):
    def in_groups(u):
        if u.is_authenticated:
            if len(u.groups.filter(name__in=group_names)) > 0:
                return True
        return False
    return user_passes_test(in_groups)

def logout_page(request):
    if request.user is not None:
        logout(request)
    return redirect('../')


def login_page(request):
    if request.user.is_authenticated:
        return redirect('shop')
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
                return redirect('shop')
            else:
                print('User not found')
        else:
            # If there were errors, we render the form with these
            # errors
            return render(request, 'login.html', {'form': form}) 
   
    return render(request,'login.html',{'form':form})

def index(request):
    return render(request,'index.html')

def signup(request):
    rand_key = hashlib.sha1(bytes(str(random.choices(string.ascii_letters,k=16)),'utf-8')).hexdigest()
    print(f"generated randomKey : {rand_key}")
    if request.method == 'POST':
        form = SignupForm(request.POST,initial={'cryptographic_key': rand_key})
        print(f"SIGNUP_FORM_NEW valid? {form.is_valid()}")
        print(form.errors)
        if form.is_valid():
            create_user_from_form(form)            
            user = User.objects.get(username=form.cleaned_data.get('username'))
            if form.cleaned_data.get('cryptographic_key') != rand_key:
                crypt_key = form.cleaned_data.get('cryptographic_key')
            print(f"CREATED USER WITH NAME: {user.username} and PASSWORD: {form.cleaned_data.get('password1')}")
            #currently working. fix soon for performance!
            h_user = HashUser.User(
                form.cleaned_data.get('first_name'),
                form.cleaned_data.get('last_name'),
                form.cleaned_data.get('email'),
                form.cleaned_data.get('password1'),
                form.cleaned_data.get('password2'),
                form.cleaned_data.get('username'),
                )
            user.profile.cryptographic_key = crypt_key
            user.profile.first_name = user.first_name
            user.profile.last_name = user.last_name
            user.profile.save()
            print(h_user.gen_sha1(level=2,salt=776))
            if crypt_key == h_user.gen_sha1(level=2,salt=776):
                permissionsModels = ['_profile']
                permissionsOptions = ['view']
                perm = Permission.objects.filter()
                for p in perm:
                    for option in permissionsOptions:
                        for model_ in permissionsModels:
                            if(option+model_)== p.codename:
                                user.user_permissions.add(p)
                user.is_staff=True
            else:
                permissionsModels = ['_shopitem','_shoplisting']
                permissionsOptions = ['add','change','delete','view']
                perm = Permission.objects.filter()
                for p in perm:
                    for option in permissionsOptions:
                        for model_ in permissionsModels:
                            if(option+model_)== p.codename:
                                user.user_permissions.add(p)
            user.save()
            login(request, user)
            return redirect('shop')
    else:
        form = SignupForm(initial={'cryptographic_key': rand_key})
    return render(request, 'signup.html', {'form': form})

def shop(request):
    return render(request,'shop.html',{'shop_items': ShopListing.objects.all()})

def item(request,item_id):
    return render(request, 'shop_item.html', {'item': ShopListing.objects.get(pk=item_id)})

def create_item(request):
    if request.method == 'POST':
        form = ShopItemForm(request.POST,request.FILES,request.user)
        print(f"CREATE_ITEM_FORM_FROM_REQUESTS:\n")
        
        print(form.data)
        print(form.files)
        print(form.is_valid())
        print(form.errors)
        
        if form.is_valid():            
            obj = form.save(commit=False)
            obj.user = request.user
            obj.cert_licencse = form.cleaned_data.get('cert_licencse')
            obj.data = form.cleaned_data.get('data')
            obj.save()         
            return redirect('shop')
    else:
        form = ShopItemForm()
    return render(request, 'new_item.html',{'form':form})

def user_items(request):
    content_dict = {}
    content_dict['user_items'] = ShopItem.objects.filter(user=request.user)
    content_dict['user_listings'] = ShopListing.objects.filter(item__user=request.user)
    print(content_dict['user_listings'])
    #content_dict['user_bought'] = ShopListing.objects.filter(item__buyers=request.user.id)
    """
    items = ShopListing.objects.all()
    for i in items:
        print(f"ItemName: {i.item.name}\n\tBuyers:")
        if not i.buyers:
            print("\t NONE - DEBUG")
        else:
            for i,b in enumerate(i.buyers):
                print(f"{i}: {i.buyers.name}")
    """
    
    return render(request,'user_items.html',content_dict)

def create_listing(request,item_id):
    if request.method == 'POST':
        form = ShopListingForm(request.POST,request.FILES,request.user)
        print(f"ENLIST_FORM valid? {form.is_valid()}\n{form.cleaned_data}")
        if form.is_valid():
            obj = form.save(commit=False)
            obj.item = ShopItem.objects.get(pk=item_id)
            obj.description = form.cleaned_data.get('description')
            obj.sold = 0
            obj.save()
            return redirect('shop')
    else:
        form = ShopListingForm()
    return render(request, 'enlist_item.html', {'form': form,'user_item':ShopItem.objects.get(pk=item_id)})

def purchase(request,item_id):
    print(item_id)
    item = ShopListing.objects.get(pk=item_id)

    buyer = request.user
    if buyer.profile.balance >= item.price:
        item.item.user.profile.balance += item.price
        buyer.profile.balance -= item.price
        set_buyer(buyer,item.item.name)
    return redirect('shop')
    

def item_page(request,item_id):
    return render(request, 'item_details.html', {'item': ShopItem.objects.get(pk=item_id)})


def review(request,item_id):
    return redirect('shop')

#has to be removed before deployment
def debug_env_variables(request):
    print(f"\n\n\n{request.META['REMOTE_ADDR']}\n\n\n")
    general = {
        'REQUEST_ORIGIN_IP': request.META['REMOTE_ADDR'],
        'REQUEST_ORIGIN_PORT': request.META['REMOTE_PORT'],
        'SECRET_KEY2': settings.SECRET_KEY2,
        'DEBUG_MODE': settings.DEBUG,
        'DEBUG_STR': settings.DEBUG_STR,
        'ENV_DB_PORT_TYPE': settings.ENV_DB_PORT_TYPE
    }
    database = settings.DATABASES['test']
   
    return render(request,'env.html',{'general':general,'db':database})


def take_notes(request):
    if request.method == 'POST':
        form = NoteForm(request.POST,initial={'notes':request.user.profile.notes})
        print(f"NoteForm valid? {form.is_valid()}\n{form.cleaned_data}")
        if form.is_valid():
            profile = Profile.objects.get(pk=request.user.id)
            profile.notes = form.cleaned_data.get('notes')
            profile.save()
            return redirect('index')
    else:
        form = NoteForm(initial={'notes':request.user.profile.notes})
    return render(request, 'notes.html', {'form': form})
    

def gift_code(request):
    if request.method == 'POST':
        form = GiftForm(request.POST,request.USER)

        print("POST")
    else:
        form = GiftForm()
    return render(request, 'giftcode.html', {'form': form})