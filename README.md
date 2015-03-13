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

### Deployment
Here's some instructions to help you get started. This has a ways to go.
- Install redis, start the daemon, and configure it to start at boot
- Run `sudo pip install -r requirements.txt` to install requirements
- Copy `wuvt/config.py.example` to `wuvt/config.py` and edit it to match your desired config
- Run `python2 create.py` to seutp the website
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

#### Templates and Static
For content in the `wuvt/templates` directory:

    Copyright 2012-2015 James Schwinabart, Calvin Winkowski, Matt Hazinski.

    Licensed under the Creative Commons Attribution-NonCommercial-NoDerivatives 
    4.0 International


