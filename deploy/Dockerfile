FROM python:3.10

WORKDIR /app/src

RUN apt-get update && apt-get install -y gettext

COPY ./requirements.txt requirements.txt
RUN pwd
RUN pip install django-modeltranslation
RUN pip install django-ace
# RUN python3 manage.py migrate
RUN pip install --upgrade pip setuptools \
    && pip install -r requirements.txt
RUN apt-get update && apt-get install -y gettext && apt-get install -y curl
