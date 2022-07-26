# Pixelspace Documentation

1. What is Pixelspace?
2. Architecture
2.1 Setup
2.2 Models
3. Vulnerability (Unicode Case Collision)
3.1. Collisions
3.2. Code
3.3. Exploit
3.4. Fix
4. Vulnerability (Race Condition)
4.1 Code
4.2 Exploit
4.3 Fix

## 1. What is Pixelspace?
Pixelspace is a microservice designed for Enowars 6. The basic functionality of this Pixelspace is buying and selling images with their corresponding license in the shop of the service. Furthermore, users can take and display private notes, as well as write and look at written reviews on the items that can be bought within the shop.
## 2. Architecture
### 2.1 Setup
Pixelspace is written in synchronous Python3 with the Django Framework. The service is split up into four Docker containers, namely:
-	Pixelspace 
-	Pixelspace_db
-	Pixelspace_redis
-	Pixelspace_rev_proxy

The **Pixelspace_db** container hosts a Postgres database (Version 14.0) and is solely used as a data storage which is attached to the **Pixelspace** WSGI application (via Django Version 3.2). The Pixelspace-Service is run by 4 *gthread* gunicorn workers (with 4 threads each), while the **Pixelspace_rev_proxy** hosts an *nginx* instance. The **Pixelspace_redis** hosts a *Redis* instance, which is used for session-tracking to relieve some stress of the Postgres database (this is necessary due to the synchronous architecture of the Pixelspace-Service). Due to the synchronous architecture and the huge amount of datasets, that will be created while running a CTF, the **Pixelspace** container also hosts a cronjob that deletes all users and their `shopItem`s and therefore all `shopListing`s based on the `expiration_date` defined via the `Profile`. **While not recommended,** the cronjob can be disabled for testing purposes and is defined in the `settings.py`. Adding a comment tag to the following lines and rebuilding the service will prohibit the creation and execution of the cronjob:

```python:
CRONJOBS = [
    ('*/0,12,24,36,48 * * * *','pixels.cron.clean_up','>> /var/log/clean_up.log')
]
```


### 2.2 Models
The **Pixelspace-Service** uses object models defined in the `models.py`. This chapter will provide a basic overview about the object classes used within the **Pixelspace-Service**.

#### Profile
The `Profile`-model extends Django's default 'User' model from `django.contrib.auth.models`. Each *Pixelspace-User* will have exactly one `Profile` attached to itself. To model this behavior a `OneToOneField` is used. Furthermore, each user will have a `balance` associated with itself defined via the `Profile`. On creation each user will have a balance of 100 by default. Additionally each `Profile` has a `notes` and a `expiration_date` attribute. The notes attribute is used at the `notes` endpoint and serves as an option to write something down for later use. The `expiration_date` defines up from which point in time the aforementioned cronjob is eligible to delete a user on its next cleanup run.

#### ShopItem
The `shopItem`-model serves as a private buffer object, before enlisting in the shop of the **Pixelspace-Service**. A user has the ability to create a new `shopItem` through the `new_item` endpoint, when authenticated. Here, the user needs to specify a name and select two upload files: the `license` and `data`. Whilst the `license` has to be a a plain text file format (i.e. txt), the `data`s filetype must be one of the following: jpg, bmp, tga or png. Furthermore, the `license` **and** `data` must be smaller than 1000 bytes in order to be valid.

#### ShopListing
Since the `shopItem`-model is only privately accessible, the `shopListing`-model serves as its public counterpart. A user can enlist each of her previously created `shopitem`s exactly once. Therefore, a `description` and the `price` have to be defined. This can be accessed via the `user_items/enlist/<item_id>` endpoint.
    
#### Buyers
The `Buyers`-model acts as a container. Each `Buyers`-object has three attributes, namely: `user`, `item`, `data`. When a user decides to purchase an item a new `Buyers`-object is created. Obviously the `user` will be filled with a reference to the user that bought the specified item, while the `item` will be filled with a reference to the `shopItem` referenced via the `shopListing.item` attribute of the purchased item. The `date` will be filled with the date information of the point in time the purchase was made. The creation of a `Buyers` instance can be found in chapter **3.2** .

#### Comment
Once a user purchased an item, he or she can leave a review. These reviews can be made via the `user_items/review/<item_id>` and will be visible at the `shop/item/<item_id>` endpoint. The `user` and `item` attribute of the `Comment`-obejct are set identically as in the `Buyers`-model. Furthermore, a review *must*
contain a rating (`comment.stars`) with an integer value between 0 and 5. Additionally a review text must be provided with a maximum length of 200 characters. On creation of a `Comment` instance the `date` of creation will be set (again similar to  the `Buyers`-model).

## 3. Vulnerability (Unicode Case Collision)
A unicode-case (mapping) collision appears when unicode and utf-8 encoded data is mixed and not handled properly. This can only occour to single byte characters. 

### 3.1 Collisions
The previously mentioned conditions on the vulnerability limit the *usable* collisions to a few characters. A list of the characters used within the *checker* can be found in the table below:

| Original character | unicode character | unicode character \(int\) |
|:------------------:|:-----------------:|:-------------------------:|
| i                  | ı                 | 305                       |
| s                  | ſ                 | 383                       |
| ss                 | ß                 | 223                       |
| m                  | µ                 | 181                       |



### 3.2 Code
The code causing this vulnerability can be found in the `util.py` and is shown below:
```python:
def set_buyer(user: User, name: str) -> bool:
    item = ShopItem.objects.raw('SELECT * FROM pixels_shopitem WHERE upper(name) = %s',[name.upper()])[0]
    buyer = Buyers.objects.create(
                user = user,
                item=item,
                data=datetime.strftime(datetime.now(), "%d/%m/%y %H:%M")
            )
    buyer.save()
```



### 3.3 Exploit
A working, coded exploit can be found within the `checker.py`. Therefore, a description about the exploit procedure will be given here:

1. Create an account via the `signup` endpoint (from now on *exploit-provider*).
2. Search for an item to exploit which contains one of the characters from the table above (this is not case-sensitive).
3. Create a `shopItem` with the *exploit-provider*-account which has a similar name to the item from step 2, but contains a unicode-character. 
    Example: If the item selected in step 2 is "Material", the name for the exploit would be "Materıal" 
4. Enlist the created `shopItem` in the shop. This will create a `shopListing`-object. The `shopListing.price` needs to be smaller than or equal to 100.
5. Create a second account via the `signup` endpoint (from now on *exploitee*).
6. Search for and buy the `shopListing` created in step 4.
7. Find the original item (step 2) within the `user_items` endpoint and view its license from the `/user_items/license/<item_id>` endpoint. The license will contain the flag.


### 3.4 Fix
The easiest fix of the vulnerable behavior of the `set_buyer` function is as simple as removing the `upper` cast of the raw SQL-query made in that function.

```python:
item = ShopItem.objects.raw('SELECT * FROM pixels_shopitem WHERE name = %s',[name])[0]
```

Furthermore, it would be possible to write a validator function that fails whenever a unicode character is entered by the user or similar inhibitors. 

## 4. Vulnerability (Race Condition)

Fixing the unicode-case (mapping) collision will provide a valid fix when load is low and response times are fast.

### 4.1 Code
When the load on the services increases a race condition presents itself, which is caused by the following code:

```python:
def purchase(request,item_id):
    item = ShopListing.objects.raw('SELECT * FROM pixels_shoplisting WHERE id = %s',[item_id])[0]
    buyer = request.user
    buyers = Buyers.objects.raw('SELECT * FROM pixels_buyers WHERE user_id = %s AND item_id = %s',[request.session['user_id'],item_id])
    if len(buyers) > 0:
        messages.error(request,'You already purchased this item!')
        return redirect('items')

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
        return redirect('items')
    return redirect('items')
```
### 4.2 Exploit
While there is no coded exploit within the repository, the building blocks for the following exploit are already implemented. Therefore, a writeup for the exploit can be found below.

1. Create two accounts via the `signup` endpoint (following named `exploit-seller` and `exploit-buyer`).
2. Enlist a previously created `shopItem` with a price lower than or equal to 100 under use of the `exploit-seller` account.
3. Gather the info needed to purchase the new `shopListing` created in step 2.
4. Send two concurrent request against the purchase endpoint for the specified item (`shop/item/purchase/<item_id>`) with the `exploit-buyer` account.
5. Since the `exploit-buyer` won't have any balance left, create a new account and repeat the steps above with the price of the `shopListing` being doubled.
   Here, the `exploit-seller` will become the `exploit-buyer` for the next iteration.

If the race condition is fulfilled the `exploit-seller` will get balance worth two times the price of the item enlisted in step 2. Therefore, the balance of the `exploit-seller` will increase exponentially.

Since the price of all items containing a flag is between $0.85*(2^{31} -2)$ and $2^{31} -2$ a mostly consistent, winning race condition is needed to exploit the service in the way described above.

### 4.3 Fix

Adding a `select_for_update` statement will take care of the concurrent requests coming in. Therefore, the aforementioned `exploit-buyer` can only purchase the item provided by the `exploit-seller` once and no exponential accumulation of balance will be possible anymore.

```python:
item = ShopListing.objects.select_for_update().raw('SELECT * FROM pixels_shoplisting WHERE id = %s',[item_id])[0]
buyer = request.user
buyers = Buyers.objects.elect_for_update().raw('SELECT * FROM pixels_buyers WHERE user_id = %s AND item_id = %s',[request.session['user_id'],item_id])
```
