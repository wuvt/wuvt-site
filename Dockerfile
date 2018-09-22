FROM python:3

RUN apt-get update && apt-get install -y \
            git \
            libcap-dev \
            libjansson-dev \
            libpcre3-dev \
            librsvg2-bin \
            libsasl2-dev \
            libyaml-dev \
            optipng \
            uuid-dev

RUN pip install --no-cache-dir uWSGI==2.0.17

WORKDIR /usr/src/app

# install python dependencies
COPY requirements.txt /usr/src/app/
RUN pip install --no-cache-dir -r requirements.txt

# copy application
ADD migrations /usr/src/app/migrations
ADD wuvt /usr/src/app/wuvt
COPY LICENSE README.md uwsgi_docker.ini setup.py /usr/src/app/

VOLUME ["/data/config", "/data/media", "/data/ssl"]

EXPOSE 8443
ENV PYTHONPATH /usr/src/app
ENV FLASK_APP wuvt
ENV APP_CONFIG_PATH /data/config/config.json

RUN python setup.py render_svgs

CMD ["uwsgi", "--ini", "uwsgi_docker.ini"]
