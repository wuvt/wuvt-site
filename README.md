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
  and [johnny-six](https://github.com/wuvt/johnny-six).
  Upon track changes, metadata is sent to Icecast, TuneIn, and Last.fm. Logged 
  playlists are publicly available on the main website. 
- HTML5 stream player capable of smooth chained OGG playback in Webkit

### Development Environment Setup
First, clone the repo, create an empty config, and build the Docker image:

```
git clone https://github.com/wuvt/wuvt-site.git
cd wuvt-site
touch wuvt/config.py
docker build -t wuvt-site -f Dockerfile.dev .
```

Now run it:
```
docker run -it --rm -p 9090:8080 wuvt-site:latest
```

You can now access the site at http://localhost:9090/

### Development Environment Setup (non-Docker)
First, install redis and supervisord. For example, on Debian or Ubuntu:

```
apt-get install redis supervisor
```

You'll also want to get uWSGI. You need at least version 2.0.9. For example:

```
apt-get install uwsgi uwsgi-core uwsgi-plugin-python
```

Now, build the SSE offload plugin. For example, on Debian:

```
apt-get install uuid-dev libcap-dev libpcre3-dev
uwsgi --build-plugin https://github.com/unbit/uwsgi-sse-offload
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
configuration options here if you so desire. Next, you will need to create the
database and fill it with some sample content:

```
python2 create.py
python2 articles.py
```

Finally, use supervisord to start the celery worker and uWSGI workers:

```
supervisord -c supervisord_dev.conf
```

You can now access the site at http://localhost:9090/

### Production Environment Setup
Here are some example instructions to get you started. These are not complete,
so it's recommended to just use the Ansible playbook for this. 
- Install redis, start the daemon, and configure it to start at boot
- Run `sudo pip install -r requirements.txt` to install requirements
- Copy `wuvt/config.py.example` to `wuvt/config.py` and edit it to match your desired config
- Run `python2 create.py` to setup the website
- Run `python2 articles.py` to create some sample articles

(TODO: uwsgi setup)

Check-out [our ansible playbooks](https://github.com/wuvt/wuvt-ansible) for
example setup with Nginx.

Once set-up, you can visit:
- `/admin` to manage website content
- `/trackman` to enter tracks

### API
TODO

Look at submit_track.sh for an example of sending metadata to Trackman.


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
