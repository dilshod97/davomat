FROM python:3.10

WORKDIR /app

RUN apt-get update && apt-get install -y gettext

COPY ./requirements.txt /app/requirements.txt
RUN pip install --upgrade pip setuptools && pip install -r requirements.txt

# Loyiha fayllarini konteynerga nusxalash
COPY . /app

# Majburiy emas, ammo foydali
ENV PYTHONUNBUFFERED=1
