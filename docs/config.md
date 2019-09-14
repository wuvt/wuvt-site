# Configuration Options

* `REDIS_URL` - Required; URL to Redis instance used for key-value storage and cache
* `POSTS_PER_PAGE` - Number of posts to display per page
* `ARTISTS_PER_PAGE` - Number of items to display per page in artist-style listings
* `SANITIZE_SUMMARY` - Boolean indicating whether or not some HTML tags should be stripped from post summaries (content is never sanitized beyond what Flask provides)
* `STATION_NAME` - Name of the station
* `STATION_SHORT_NAME` - Shorter name of the station (i.e. just the callsign)
* `STATION_URL` - Website of the station
* `NAV_TOP_SECTIONS` - List of dictionaries describing top-level nav items
* `INTERNAL_IPS` - List of internal IP addresses that can access mission control
* `TRACKMAN_URL` - URL to the root of a functional Trackman instance
* `ADMINS` - List of email addresses that will receive error emails
* `MAIL_FROM` - Email address used for sending email
* `SMTP_SERVER` - SMTP server used for sending email
* `DONATE_MAIL_FROM` - Email address used for sending donation receipts
* `PROXY_FIX` - Boolean indicating whether or not to process X-Forwarded-For headers
* `PROXY_FIX_NUM_PROXIES` - Number of proxies used for X-Forwarded-For headers
* `MIN_PASSWORD_LENGTH` - Minimum password length required to log in for local authentication
* `UPLOAD_DIR` - Path to where media should be uploaded
* `DONATE_ENABLE` - Boolean indicating whether or not donations are enabled
* `STRIPE_NAME` - Name to use for Stripe donations
* `STRIPE_DESCRIPTION` - Description to use for Stripe donations
* `STRIPE_SECRET_KEY` - Secret key from Stripe
* `STRIPE_PUBLIC_KEY` - Public key from Stripe
* `STRIPE_MISSIONCONTROL_EMAIL` - Email address to use for mission control donations where no email is specified
* `AUTH_METHOD` - Authentication method to use (`google`, `oidc`, or `local`)
* `AUTH_SUPERADMINS` - List of OIDC subs that have access to everything
* `AUTH_ROLE_GROUPS` - Dictionary describing how application roles map to OIDC groups
* `OIDC_CLIENT_SECRETS` - Path to the OIDC `client_secrets.json` file
* `OIDC_SCOPES` - List of scopes used for OIDC (i.e. to also use groups)
* `GOOGLE_CLIENT_ID` - OAuth2 client ID for Google auth
* `GOOGLE_CLIENT_SECRET` - OAuth2 client secret for Google auth
* `GOOGLE_ALLOWED_DOMAINS` - List of allowed domains for Google auth; if not set or empty, all domains are allowed
* `GOOGLE_ADMIN_SUBJECT` - Needs to be the email address of a Google domain admin; this is required for obtaining user groups
* `GOOGLE_SERVICE_ACCOUNT_FILE` - Path to the Google service account file used for obtaining user groups
* `GOOGLE_AUTHORIZE_URL` - Optional; override authorize URL to set custom paramters

Additional configuration options are described in the documentation for [Flask](http://flask.pocoo.org/docs/1.0/config/#builtin-configuration-values), [Flask-SQLAlchemy](http://flask-sqlalchemy.pocoo.org/2.3/config/#configuration-keys), and [Flask-WTF](https://flask-wtf.readthedocs.io/en/stable/config.html).
