#!/bin/sh

if [ "$DATABASE" = "postgres" ]
then
    echo "Waiting for postgres..."

    while ! nc -z $SQL_HOST $SQL_PORT; do
      sleep 0.1
    done

    echo "PostgreSQL started"
fi

python3 manage.py collectstatic --no-input
python3 manage.py makemigrations --no-input
python3 manage.py migrate
python3 manage.py createsuperuser --username root --no-input

python3 manage.py createsuperuser --username alex --no-input
python3 manage.py createsuperuser --username michi --no-input

exec "$@"