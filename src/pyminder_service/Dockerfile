FROM ubuntu:20.04
LABEL maintainer="zadammac@kenshosec.com"


RUN apt-get update -y && apt-get install -y python3 python3-pip
COPY ./requirements.txt /app/requirements.txt

WORKDIR /app

RUN pip3 install -r requirements.txt

COPY . /app

ENTRYPOINT ["python3", "run.py"]