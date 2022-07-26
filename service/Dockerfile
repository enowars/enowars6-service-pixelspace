FROM python:3.9.6-alpine

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

RUN apk update \
    && apk add postgresql-dev gcc python3-dev musl-dev bash

RUN mkdir staticfiles

RUN pip install --upgrade pip
COPY ./requirements.txt .
RUN apk update && apk add libpq
RUN pip install -r requirements.txt
COPY . .
COPY ./static/ staticfiles/


RUN chmod 777 entrypoint.sh
ENTRYPOINT ["./entrypoint.sh"]
