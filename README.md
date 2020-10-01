## wuvt-site
This is my new generation website that is suitable for any kind of need from old to the young mindset of the world......

It includes both a basic content management and simple donation system. It also
integrates with Trackman to provide live track information and playlists.

### Deployment
These instructions are for Linux; instructions for other platforms may vary.

First, clone the repo, create an empty config, and build the appropriate Docker
image for your environment. We provide Dockerfile.dev which is configured to
use SQLite and runs Redis directly in the image, and Dockerfile, which is
recommended for production deployments as it does not run any of the required
services inside the container itself.

For Dockerfile.dev:
```
git clone https://github.com/wuvt/wuvt-site.git
cd wuvt-site
docker build -t wuvt-site -f Dockerfile.dev .
```

Now, go ahead and copy config/config_example.json to config/config.json and
configure as necessary. The most important thing is to set a random value for
`SECRET_KEY`. You can generate a random value using the following command:
```
xxd -l 28 -p /dev/urandom
```

Finally, run it:
```
docker run --rm -v $PWD/config:/data/config -e APP_CONFIG_PATH=/data/config/config.json -p 9070:8080 wuvt-site:latest
```

You can now access the site at <http://localhost:9070/>. An admin user account
will be created for you; the password is automatically generated and displayed
when you launch the container.

### Non-Docker Deployment
First, install redis. For example, on Debian or Ubuntu:

```
apt-get install redis
```

You'll also want to get uWSGI. You need at least version 2.0.9. For example:

```
apt-get install uwsgi uwsgi-core uwsgi-plugin-python
```

Now, build the SSE offload plugin. For example, on Debian:

```
apt-get install uuid-dev libcap-dev libpcre3-dev
uwsgi --build-plugin https://github.com/wuvt/uwsgi-sse-offload
sudo cp sse_offload_plugin.so /usr/lib/uwsgi/plugins/
```

Make sure the redis daemon is running; on Debian, this will happen
automatically.

It is recommended that you use a virtualenv for this so that you can better
separate dependencies:

```
mkdir -p ~/.local/share/virtualenv
virtualenv ~/.local/share/virtualenv/wuvt-site
source ~/.local/share/virtualenv/wuvt-site/bin/activate
```

Now, within this virtualenv, install the dependencies:

```
pip install -r requirements.txt
```

Next, clone the repo:

```
git clone https://github.com/wuvt/wuvt-site.git
cd wuvt-site
```

Create a blank file, wuvt/config.py; you can override any of the default
configuration options here if you so desire. You'll definitely need to set a
value for `SECRET_KEY`. Next, you will need to render images, create the
database, and add some sample content to the site:

```
export FLASK_APP=$PWD/wuvt/__init__.py
flask render_images && flask initdb && flask sampledata
```

Finally, start uWSGI:

```
uwsgi --ini uwsgi.ini:dev
```

You can now access the site at http://localhost:9070/

### License

Besides the exceptions noted below, the entirety of this software is available
under the GNU Affero General Public License:

```
Copyright 2012-2018 James Schwinabart, Calvin Winkowski, Matt Hazinski.

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU Affero General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU Affero General Public License for more details.

You should have received a copy of the GNU Affero General Public License
along with this program.  If not, see <http://www.gnu.org/licenses/>.
```

The following files are JavaScript libraries, freely available under the MIT
license as noted in their headers:
* wuvt/static/js/jquery.js
* wuvt/static/js/jquery.dataTables.min.js
* wuvt/static/js/moment.min.js

The following font file was designed by Humberto Gregorio and is in the public
domain:
* wuvt/static/fonts/sohoma_extrabold.woff

Other included fonts (in wuvt/static/fonts) are not covered under this license.
