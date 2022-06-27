# syntax=docker/dockerfile:1
FROM python:3
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
WORKDIR /code
COPY requirements.txt /code/
# install psycopg2 dependencies
RUN pip install -r requirements.txt
COPY . /code/


RUN cron
#ENTRYPOINT [ "gunicorn", "-c", "gunicorn.conf.py", "pixelspace.asgi" ]
#ENTRYPOINT [ "python3", "entrypoint.py" ]