from django.shortcuts import render,redirect
from django.http.response import FileResponse
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.forms import AuthenticationForm
from pixels.models import *
from pixels.forms import *
from pixels.util import *
from django.contrib import messages
from django.contrib.auth.models import User
from django.db import connection


def logout_page(request):
    logout(request)
    request.session['auth'] = False
    return redirect('index')

def login_page(request):
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
                request.session['user_name'] = user.username
                request.session['balance'] = user.profile.balance
                request.session['user_id'] = user.id
                request.session['auth'] = True
                return redirect('index')
        else:
            return render(request, 'login.html', {'form': form}) 
   
    return render(request,'login.html',{'form':form})

def index(request):
    return render(request,'index.html')

def signup(request):
    if request.method == 'POST':
        form = SignupForm(request.POST)
        
        if form.is_valid():      
            user = User.objects.create(
                username= form.cleaned_data.get('username'),
                first_name= form.cleaned_data.get('first_name'),
                last_name = form.cleaned_data.get('last_name')
            )
            user.set_password(form.cleaned_data.get('password1'))
            user.save()    
            login(request, user)
            request.session['user_name'] = user.username
            request.session['balance'] = user.profile.balance
            request.session['user_id'] = user.id
            request.session['auth'] = True
            return redirect('index',)
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

    items = ShopListing.objects.raw('SELECT * FROM pixels_shoplisting ORDER BY id ASC OFFSET %s ROW FETCH NEXT 5 ROWS ONLY',[((page_num -1) *5)])

    if len(items) < 5:
        next_page = None

    return render(request,'shop.html',{'shop_items':items,'prev': prev_page, 'next':next_page, 'current': page_num})

def item(request,item_id):
    avg_rating = 0
    content_dict = {}
    content_dict['item'] = ShopListing.objects.get(pk=item_id)
    
    content_dict['reviews'] = Comment.objects.raw('SELECT * FROM pixels_comment WHERE item_id = %s',[item_id])
    num_revs = len(content_dict['reviews'])
    for r in content_dict['reviews']:
        avg_rating += r.stars
    if num_revs != 0:
        avg_rating /= num_revs
    content_dict['rating'] = avg_rating
    return render(request, 'shop_item.html', content_dict)


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
            messages.success(request,f"Successfully created item with id: {item_id}")
            return redirect(f"itemDetails",item_id = item_id)
    else:
        form = ShopItemForm()
    return render(request, 'new_item.html',{'form':form})

def user_items(request):
    content_dict = {}
    content_dict['user_items'] = ShopItem.objects.filter(user=request.user)
    content_dict['user_listings'] = ShopListing.objects.filter(item__user=request.user)
    content_dict['user_bought'] = Buyers.objects.filter(user=request.user)


    return render(request,'user_items.html',content_dict)


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
            messages.success(request,f"Successfully created listing with id: {listing_id}")
            return redirect("itemPage",item_id=listing_id)
    else:
        form = ShopListingForm()
    return render(request, 'enlist_item.html', {'form': form,'user_item':ShopItem.objects.get(pk=item_id)})


def purchase(request,item_id):
    item = ShopListing.objects.raw('SELECT * FROM pixels_shoplisting WHERE id = %s',[item_id])[0]
    buyer = request.user
    buyers = Buyers.objects.raw('SELECT * FROM pixels_buyers WHERE user_id = %s AND item_id = %s',[request.session['user_id'],item_id])
    if len(buyers) > 0:
        messages.error(request,'You already purchased this item!')
        return redirect('index')

    if request.user == item.item.user:
        messages.error(request,'You cannot buy your own item!')
        return redirect('shop',page_num=1)
    balance = buyer.profile.balance
    if balance >= item.price:
        item.item.user.profile.balance += item.price
        item.item.user.profile.save()
        balance -= item.price
        request.session['balance'] = balance
        buyer.profile.balance = balance
        buyer.profile.save()
        set_buyer(buyer,item.item.name)
        item.sold +=1
        messages.success(request,f"Successfully bought item: {item.item.name} ({item.item.pk})")
        item.save()
    else:
        messages.error(request,'You cannot aford to buy this item!')
        return redirect('index')
    return redirect('index')
    

def item_page(request,item_id):


    return render(request, 'item_details.html', {'item': ShopItem.objects.get(id=item_id)})


def review(request,item_id):
    if request.method == 'POST':
        form = CommentForm(request.POST)
        if form.is_valid():
            com = form.save(commit=False)
            reception = Comment.objects.create(
                item = ShopListing.objects.raw('SELECT * FROM pixels_shoplisting WHERE item_id = %s',[item_id])[0],
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
                cursor.execute("UPDATE pixels_profile SET notes = %s WHERE user_id = %s",[notes,request.session['user_id']])            
            return redirect('items')
    else:
        form = NoteForm(initial={'notes':request.user.profile.notes})
    return render(request, 'notes.html', {'form': form})
   
def license_access(request, item_id):    
    access_granted = False
    user = request.user
    item = ShopItem.objects.get(pk=item_id)
    if request.session['auth']:
        if user == item.user:
            response = FileResponse(item.cert_license)
            return response
        buyers = Buyers.objects.raw('SELECT * FROM pixels_buyers WHERE item_id = %s AND user_id = %s',[item.pk,request.session['user_id']])
        if len(buyers) > 0:
            access_granted = True  
    if access_granted:
        response = FileResponse(item.cert_license)
        return response
    else:
        messages.error(request,'You are not allowed to view this content!')
        return redirect('index')
    
