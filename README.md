## wuvt-site
This is the next-generation website for [WUVT-FM](https://www.wuvt.vt.edu), 
Virginia Tech's student radio station.

It has several main components:
- A Content Management System (CMS) to store both blog-style *articles* and 
  static *pages*. These can be managed at the `/admin` endpoint. One *admin*
  user capable of administrative access exists; all other users have full 
  control of articles and pages and may upload files. 
- **Trackman**, a track logger with a UI and an API compatible with both 
  WinAmp's POST plugin and [mpd-automation](https://github.com/wuvt/mpd-automation). 
  Upon track changes, metadata is sent to Icecast, TuneIn, and Last.fm. Logged 
  playlists are publicly available on the main website. 
- HTML5 stream player capable of smooth chained OGG playback in Webkit

### Development Environment Setup
Install redis and start the daemon. You'll need redis running whenever you want
to run the site, but it is not necessary to start it on boot.

It is recommended that you use a virtualenv for this so that you can better
separate dependencies:

```
mkdir -p ~/.local/share/virtualenv
virtualenv ~/.local/share/virtualenv/wuvt-site
source ~/.local/share/virtualenv/bin/activate
```

Now, within this virtualenv, install the dependencies:

```
pip install -r requirements.txt
```

You'll also want to get gunicorn, which is used as a local web server:

```
pip install gunicorn
```

Next, clone the repo and make a copy of the config:

```
git clone https://github.com/wuvt/wuvt-site.git
cd wuvt-site
cp wuvt/config.py.example wuvt/config.py
```

Edit wuvt/config.py to match your desired config, then go ahead and create the
database and fill it with some sample content:

```
python2 create.py
python2 articles.py
```

Finally, start the celery worker and development web server:

```
./run_celery.sh &
./run_dev_server.sh
```

You can now access the site at http://127.0.0.1:8080/

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

#### Default
For everything **except** the `wuvt/templates` and `wuvt/static` 
directories:

```
Copyright 2012-2015 James Schwinabart, Calvin Winkowski, Matt Hazinski.

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

   http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
```

#### Templates and Static
For content in the `wuvt/templates` directory:

```
Copyright 2012-2015 James Schwinabart, Calvin Winkowski, Matt Hazinski.

Licensed under the Creative Commons Attribution-NonCommercial-NoDerivatives 
4.0 International
```
