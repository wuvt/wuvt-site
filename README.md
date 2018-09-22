## wuvt-site
This is the next-generation website for [WUVT-FM](https://www.wuvt.vt.edu), 
Virginia Tech's student radio station.

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
echo "SECRET_KEY = \"$(xxd -l 28 -p /dev/urandom)\"" > wuvt/config.py
```

Now run it:
```
docker-compose up
```

You can now access the site at <http://localhost:9070/>. An admin user account
will be created for you; the password is automatically generated and displayed
when you launch the container.

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
