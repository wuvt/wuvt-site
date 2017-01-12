## wuvt-site
This is the next-generation website for [WUVT-FM](https://www.wuvt.vt.edu), 
Virginia Tech's student radio station.

It has several main components:
- A Content Management System (CMS) to store both blog-style *articles* and 
  static *pages*. These can be managed at the `/admin` endpoint. One *admin*
  user capable of administrative access exists; all other users have full 
  control of articles and pages and may upload files. 
- **Trackman**, a track logger with a UI and an API compatible with WinAmp's
  POST plugin, [mpd-automation](https://github.com/wuvt/mpd-automation),
  and [johnny-six](https://github.com/wuvt/johnny-six). The included SSE
  endpoint can be used by external scripts for live track updates, similar to
  how it is used on the website. It also provides access to previous playlists
  and can generate charts of what has been played.
- A simple donation system with Stripe integration for processing credit
  card/Bitcoin transactions.

### Deployment
First, clone the repo, create an empty config, and build the appropriate Docker
image for your environment. We provide Dockerfile.dev which is configured to
use SQLite and runs Redis directly in the image, and Dockerfile, which is
recommended for production deployments as it does not run any of the required
services inside the container itself.

For Dockerfile.dev:
```
git clone https://github.com/wuvt/wuvt-site.git
cd wuvt-site
touch wuvt/config.py
docker build -t wuvt-site -f Dockerfile.dev .
```

Now run it:
```
docker run --rm -p 9090:8080 wuvt-site:latest
```

You can now access the site at http://localhost:9090/

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
configuration options here if you so desire. Next, you will need to render
images, create the database, and add some sample content to the site:

```
export FLASK_APP=$PWD/wuvt/__init__.py
flask render_images && flask initdb && flask sampledata
```

Finally, start uWSGI:

```
uwsgi --ini uwsgi.ini:dev
```

You can now access the site at http://localhost:9090/

### API
TODO

Look at submit_tracks.py for an example of sending metadata to Trackman.


### License

Besides the exceptions noted below, the entirety of this software is available
under the GNU Affero General Public License:

```
Copyright 2012-2016 James Schwinabart, Calvin Winkowski, Matt Hazinski.

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
