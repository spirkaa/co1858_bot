FROM python:3.5-alpine

ENV PYTHONUNBUFFERED 1

# Requirements have to be pulled and installed here, otherwise caching won't work
COPY requirements.txt /

RUN apk add --no-cache \
        tzdata \
        libxslt-dev \
        libxml2-dev \
        libffi-dev \
        openssl-dev \
     && ln -sf /usr/share/zoneinfo/Europe/Moscow /etc/localtime \
     && apk add --no-cache --virtual .build-deps \
        build-base \
		python3-dev

RUN pip install --no-cache-dir -U -r /requirements.txt

RUN apk del .build-deps

COPY ./app /app

WORKDIR /app

CMD python ./bot.py | python ./db_update.py
