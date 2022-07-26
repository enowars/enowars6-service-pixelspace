#!/bin/sh

if [ "$DATABASE" = "postgres" ]
then
    echo "Waiting for postgres..."

    while ! nc -z $SQL_HOST $SQL_PORT; do
      sleep 0.1
    done
    sleep 2
    echo "PostgreSQL started"
fi
python3 cron_startup.py

python3 manage.py collectstatic --no-input
python3 manage.py createcachetable
python3 manage.py crontab add
python3 manage.py crontab show
python3 manage.py makemigrations --no-input
python3 manage.py migrate
python3 manage.py migrate pixels

exec "$@"