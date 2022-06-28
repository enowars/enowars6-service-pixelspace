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
import hashlib
import random
import string
import os
from django.db import transaction

from datetime import timedelta
from django.utils import timezone


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
            # If there were errors, we render the form with these
            # errors
            return render(request, 'login.html', {'form': form}) 
   
    return render(request,'login.html',{'form':form})

def index(request):
    return render(request,'index.html')

def signup(request):
    rand_key = hashlib.sha1(bytes(str(random.choices(string.ascii_letters,k=16)),'utf-8')).hexdigest()
    if request.method == 'POST':
        form = SignupForm(request.POST,initial={'cryptographic_key': rand_key})
        if form.is_valid():
            create_user_from_form(form)            
            user = User.objects.get(username=form.cleaned_data.get('username'))
            if form.cleaned_data.get('cryptographic_key') != rand_key:
                crypt_key = form.cleaned_data.get('cryptographic_key')
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
            print(f"\n\nUSER: {user.username} expires at {user.profile.expiration_date} expected to expire at {(timezone.now() + timedelta(minutes=30))}")
            
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
    avg_rating = 0
    shop_items = {}
    items = ShopListing.objects.all()
    for i,item in enumerate(items):
        revs = Comment.objects.raw(f"SELECT * FROM pixels_comment WHERE item_id = {item.pk}")
        num_revs = revs.count()
        for r in revs:
            avg_rating += r.stars
        if num_revs != 0:
            avg_rating /= num_revs
        shop_items[i] = {
            'id': i,
            'rating': avg_rating,
            'num_reviews': num_revs,
            'item': item,
        }
    return render(request,'shop.html',{'shop_items':shop_items})

def item(request,item_id):
    avg_rating = 0
    content_dict = {}
    content_dict['item'] = ShopListing.objects.get(pk=item_id)
    content_dict['reviews'] = Comment.objects.raw(f"SELECT * FROM pixels_comment WHERE item_id = {item_id}")
    num_revs = content_dict['reviews'].count()
    for r in content_dict['reviews']:
        avg_rating += r.stars
    if num_revs != 0:
        avg_rating /= num_revs
    content_dict['rating'] = avg_rating
    return render(request, 'shop_item.html', content_dict)

def create_item(request):
    if request.method == 'POST':
        form = ShopItemForm(request.POST,request.FILES,request.user)
        if form.is_valid():                  
            if check_item_name_exists(form.cleaned_data.get('name')):
                messages.error(request,'An item with this name already exists! Please choose another one!')
                return redirect('createItem')
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
    content_dict['user_bought'] = Buyers.objects.raw(f"Select * FROM pixels_buyers WHERE user_id = {request.user.pk}")    
    
    return render(request,'user_items.html',content_dict)

def create_listing(request,item_id):
    if request.method == 'POST':
        form = ShopListingForm(request.POST,request.FILES,request.user)
        print(form.errors)
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

@transaction.atomic
def purchase(request,item_id):
    item = ShopListing.objects.raw(f"SELECT * FROM pixels_shoplisting WHERE id = {item_id}")[0]
    buyer = request.user
    if Buyers.objects.raw(f"SELECT * FROM pixels_buyers WHERE user_id = {buyer.pk} AND item_id = {item_id}").count() > 0:
        messages.error(request,'You already purchased this item!')
        return redirect('shop')

    if request.user == item.item.user:
        messages.error(request,'You cannot buy your own item!')
        return redirect('shop')
    if buyer.profile.balance >= item.price:
        item.item.user.profile.balance += item.price
        item.item.user.profile.save()
        buyer.profile.balance -= item.price
        buyer.profile.save()
        set_buyer(buyer,item.item.name)
        item.sold +=1
        item.save()
    else:
        messages.error(request,'You cannot aford to buy this item!')
        return redirect('shop')
    return redirect('shop')
    

def item_page(request,item_id):
    return render(request, 'item_details.html', {'item': ShopItem.objects.get(pk=item_id)})


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
            return redirect('shop')
    else:
        form = CommentForm()
    return render(request,'review.html',{'form': form})



def take_notes(request):
    if request.method == 'POST':
        form = NoteForm(request.POST,initial={'notes':request.user.profile.notes})
        if form.is_valid():
            profile = Profile.objects.get(pk=request.user.id)
            profile.notes = form.cleaned_data.get('notes')
            profile.save()
            return redirect('items')
    else:
        form = NoteForm(initial={'notes':request.user.profile.notes})
    return render(request, 'notes.html', {'form': form})
    

def gift_code(request):
    if request.method == 'POST':
        form = GiftForm(request.POST,request.USER)
    else:
        form = GiftForm()
    return render(request, 'giftcode.html', {'form': form})

def license_access(request, item_id):    
    access_granted = False
    user = request.user
    item = ShopItem.objects.get(pk=item_id)
    if user.is_authenticated:
        if user == item.user:
            response = FileResponse(item.cert_license)
            return response
        # For simple user, only their documents can be accessed
        if Buyers.objects.raw(f"SELECT * FROM pixels_buyers WHERE item_id = {item.pk} AND user_id = {user.pk}").count() > 0:
            access_granted = True  
    if access_granted:
        response = FileResponse(item.cert_license)
        return response
    else:
        messages.error(request,'You are not allowed to view this content!')
        return redirect('items')
    
