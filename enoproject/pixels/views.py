from django.shortcuts import render,redirect
from django.http import HttpResponse,HttpResponseRedirect
from django.urls import reverse
# Create your views here.

from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.decorators import user_passes_test
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth.models import Permission
from pixels.models import *
from pixels.forms import *
from pixels.util import *

def group_required(*group_names):
    def in_groups(u):
        if u.is_authenticated:
            if len(u.groups.filter(name__in=group_names)) > 0:
                return True
        return False
    return user_passes_test(in_groups)

@group_required("admin_group")
def server_seed(request):
    return render(request,'seed.html')


def logout_page(request):
    if request.user is not None:
        logout(request)
    return  render(request,'index.html')


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
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            form.save()
            username = form.cleaned_data.get('username')
            raw_password = form.cleaned_data.get('password1')
            user = authenticate(username=username, password=raw_password)

            #currently working. fix soon for performance!
            permissionsModels = ['_shopitem','_shoplisting']
            permissionsOptions = ['add','change','delete','view']
            perm = Permission.objects.filter()
            for p in perm:
                for option in permissionsOptions:
                    for model_ in permissionsModels:
                        if(option+model_)== p.codename:
                            user.user_permissions.add(p)
            login(request, user)
            return redirect('shop')
    else:
        form = UserCreationForm()
    return render(request, 'signup.html', {'form': form})

def shop(request):
    return render(request,'shop.html',{'shop_items': ShopListing.objects.all()})

def item(request,item_id):
    return render(request, 'shop_item.html', {'item': ShopListing.objects.get(pk=item_id)})

def create_item(request):
    if request.method == 'POST':
        form = ShopItemForm(request.POST,request.FILES,request.user)
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
    print(content_dict)
    return render(request,'user_items.html',content_dict)

def create_listing(request,item_id):
    if request.method == 'POST':
        form = ShopListingForm(request.POST,request.FILES,request.user)
        print(f"ENLIST_FORM valid? {form.is_valid()}\n{form.cleaned_data}")
        if form.is_valid():
            obj = form.save(commit=False)
            obj.item = ShopItem.objects.get(pk=item_id)
            obj.description = form.cleaned_data.get('description')
            obj.buyers = "0="
            obj.sold = 0
            obj.available_units = form.cleaned_data.get('available_units')
            obj.save()
            return redirect('shop')
    else:
        form = ShopListingForm(),
    return render(request, 'enlist_item.html', {'form': form,'user_item':ShopItem.objects.get(pk=item_id)})

def purchase(request,item_id):
    print(item_id)
    item = ShopListing.objects.get(pk=item_id)

    buyer = request.user
    if buyer.profile.balance >= item.price and item.sold < item.available_units:
        buyer.profile.balance -= item.price
        item.item.user.profile.balance += item.price
        set_buyer(buyer,item.item.name)
        return redirect('shop')
    return redirect('shop')