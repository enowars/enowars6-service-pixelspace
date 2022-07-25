# Pixelspace Documentation

1. What is Pixelspace?
2. Architecture
3. Vulnerability (Unicode Case Collision)
3.1. Collisions
3.2. Code
3.3. Exploit
3.4. Fix
4. Vulnerability (Race Condition)
4.1 Code
4.2 Exploit
4.3 Fix
5. Further Information

## What is Pixelspace?
Pixelspace is a microservice designed for Enowars 6. The basic functionality of this Pixelspace is buying and selling images with their corresponding license in the shop of the service. Furthermore, users can take and display private notes, as well as write and look at written reviews on the items that can be bought within the shop.
## Architecture
Pixelspace is written in synchronous Python3 with the Django Framework. The service is split up into four Docker containers, namely:
-	Pixelspace 
-	Pixelspace_db
-	Pixelspace_redis
-	Pixelspace_rev_proxy

The **Pixelspace_db** container hosts a Postgres database (Version 14.0) and is solely used as a data storage which is attached to the **Pixelspace** WSGI application (via Django Version 3.2). The Pixelspace-Service is run by 4 *gthread* gunicorn workers (with 4 threads each), while the **Pixelspace_rev_proxy** hosts an *nginx* instance. The **Pixelspace_redis** hosts a *Redis* instance, which is used for session-tracking to relieve some stress of the Postgres database (this is necessary due to the synchronous architecture of the Pixelspace-Service).


HERE MORE ABOUT SERVICE AND DATA-MODEL ARCHITECTURE

## Vulnerability (Unicode Case Collision)
A unicode-case (mapping) collision appears when unicode and utf-8 encoded data is mixed and not handled properly. This can only occour to single byte characters. 

### Collisions
The previously mentioned conditions on the vulnerability limit the *usable* collisions to a few characters. A list of the characters used within the *checker* can be found in the table below:

| Original character | unicode character | unicode character \(int\) |
|:------------------:|:-----------------:|:-------------------------:|
| i                  | ı                 | 305                       |
| s                  | ſ                 | 383                       |
| ss                 | ß                 | 223                       |
| m                  | µ                 | 181                       |


HOW DOES A COLLISION OCCOUR -> bitwise comparison

### Code
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



### Exploit
A working, coded exploit can be found within the `checker.py`. Therefore, a description about the exploit procedure will be given here:

1. Create an account via the `signup` endpoint (from now on *exploit-provider*).
2. Search for an item to exploit which contains one of the characters from the table above (this is not case-sensitive).
3. Create a `shopItem` with the *exploit-provider*-account which has a similar name to the item from step 2, but contains a unicode-character. (Example)
4. Enlist the created `shopItem` in the shop. This will create a `shopListing`-object. The `shopListing.price` needs to be smaller than or equal to 100.
5. Create a second account via the `signup` endpoint (from now on *exploitee*).
6. Search for and buy the `shopListing` created in step 4.
7. Find the original item (step 2) within the `user_items` endpoint and view its license from the `/user_items/license/<item_id>` endpoint. The license will contain the flag.


### Fix
The easiest fix of the vulnerable behavior of the `set_buyer` function is as simple as removing the `upper` cast of the raw SQL-query made in that function.

```python:
item = ShopItem.objects.raw('SELECT * FROM pixels_shopitem WHERE name = %s',[name])[0]
```

Furthermore, it would be possible to write a validator function that fails whenever a unicode character is entered by the user or similar inhibitors. 

## Vulnerability (Race Condition)

Fixing the unicode-case (mapping) collision will provide a valid fix 
