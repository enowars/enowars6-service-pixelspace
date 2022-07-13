You may create a superuseraccount with the following commands:

docker exec -it Pixelspace bash

In the default directory of the container run:

python3 manage.py createsuperuser

A cronjob runs a cleanup-Task every 12 minutes and deletes all users that have an expiration-date < runtime.