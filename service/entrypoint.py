import os
import time
import json


PRODUCTION = True


#Migrate django application if needed
print("\n\nCHECKING FOR DATABASE CHANGES\n\n")
os.system("python3 manage.py collectstatic")
os.system("python3 manage.py makemigrations")
os.system("python3 manage.py migrate")




if PRODUCTION:
    print("\n\nSTARTING --PRODUCTION-- ENVIRONMENT OF PIXELSPACE\n\n")
    time.sleep(2)
    #os.environ['DEBUG_MODE'] = "False"
    #Startup service with gunicorn
    os.system("gunicorn -c gunicorn.conf.py pixelspace.asgi")
else:
    print("\n\nSTARTING --DEVELOPMENT-- ENVIRONMENT OF PIXELSPACE\n\n")
    time.sleep(2)
    #os.environ['DEBUG_MODE'] = "True"
    os.system("python3 manage.py runserver 0.0.0.0:8010")
