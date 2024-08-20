FROM python:3.10.14-slim

COPY . /var/app

WORKDIR /var/app

RUN apt update
RUN apt install libpq-dev python3-dev build-essential minicom -y
RUN pip install -r requirements.txt

