import os
import time


PRODUCTION = True


#Migrate django application if needed
print("\n\nCHECKING FOR DATABASE CHANGES\n\n")
os.system("python3 manage.py makemigrations")
os.system("python3 manage.py migrate")

#setup test db data
os.environ['TEST_NAME'] = "test_db"
os.environ['TEST_USER'] = "test_db_user"
os.environ['TEST_PASSWORD'] = "test_db_password"
os.environ['TEST_HOST'] = "test_db_host"
os.environ['TEST_DB_PORT'] = "2022"


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
