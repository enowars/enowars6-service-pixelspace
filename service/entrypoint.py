import os
import time


PRODUCTION = True


#setup test db data
os.environ['TEST_ENGINE'] = "django.db.backends.postgresql"
os.environ['TEST_NAME'] = os.environ.get('POSTGRES_NAME')
os.environ['TEST_USER'] = os.environ.get('POSTGRES_USER')
os.environ['TEST_PASSWORD'] = os.environ.get('POSTGRES_PASSWORD')
os.environ['TEST_HOST'] = "pixelspace_db"
os.environ['TEST_DB_PORT'] = "5432"

#Migrate django application if needed
print("\n\nCHECKING FOR DATABASE CHANGES\n\n")
os.system("python3 manage.py makemigrations")
os.system("python3 manage.py migrate")




if PRODUCTION:
    print("\n\nSTARTING --PRODUCTION-- ENVIRONMENT OF PIXELSPACE\n\n")
    time.sleep(2)
    os.environ['DEBUG_MODE'] = "False"
    #Startup service with gunicorn
    os.system("gunicorn -c gunicorn.conf.py pixelspace.asgi")
else:
    print("\n\nSTARTING --DEVELOPMENT-- ENVIRONMENT OF PIXELSPACE\n\n")
    time.sleep(2)
    os.environ['DEBUG_MODE'] = "True"
    os.system("python3 manage.py runserver 0.0.0.0:8010")
