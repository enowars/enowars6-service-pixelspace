# Pixelspace Documentation

1. What is Pixelspace?
2. Architecture
3. Vulnerability (Unicode Case Collision)
3.1. Collisions
3.2. Code
3.3. Exploit
3.4. Fix
5. Further Information

## What is Pixelspace?
Pixelspace is a microservice designed for Enowars 6. The basic functionalitiy of this Pixelspace is buying and selling images with their corresponding license in the shop of the service. Furthermore users can take and display private notes and write and look at written reviews on the items that can be bought within the shop.
## Architecture
Pixelspace is written in synchronous Python3 with the Django Framework. The service is split up into four Docker containers, namely:
-	Pixelspace 
-	Pixelspace_db
-	Pixelspace_redis
-	Pixelspace_rev_proxy

The **Pixelspace_db** container hosts a Postgres database (Version 14.0) and is solely used as a data storage which is attached to the **Pixelspace** WSGI application (via Django Version 3.2). The Pixelspace-Service is run by 4 *gthread* gunicorn workers (with 4 threads each), while the **Pixelspace_rev_proxy** hosts an *nginx* instance. The **Pixelspace_redis** hosts a *Redis* instance, which is used for session-tracking to relieve some stress of the Postgres database (this is necessary due to the synchronous architecture of the Pixelspace-Service).




## Vulnerability (Unicode Case Collision)
A unicode-case (mapping) collision appears when unicode and utf-8 encoded data is mixed and inproperly handled. This can only occour to single byte characters. 

### Collisions
The previously mentioned conditions on the vulnerability limit the *useable* collisions to a few characters. A list of the characters used within the *checker* can be found below:



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
A working, coded exploit can be found within the `checker.py`. Therefore, a description about the exploit procedure will be given here.

1. 

### Fix

