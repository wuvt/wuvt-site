DEBUG = False
# SESSION_COOKIE_SECURE = True

SQLALCHEMY_TRACK_MODIFICATIONS = False
REDIS_URL = 'redis://redis:6379/0'

POSTS_PER_PAGE = 5
ARTISTS_PER_PAGE = 500
SANITIZE_SUMMARY = True

STATION_NAME = "WUVT-FM 90.7 Blacksburg, VA"
STATION_SHORT_NAME = "WUVT-FM"
STATION_URL = "https://www.wuvt.vt.edu"
NAV_TOP_SECTIONS = [
    {'menu': 'about',
     'name': 'About',
     'slug': 'wuvt'},
    {'menu': 'community',
     'name': 'Community'},
    {'menu': 'playlists',
     'name': 'Playlists'},
    {'menu': 'shows',
     'name': 'Shows'},
    {'menu': 'contact',
     'name': 'Contact'},
    {'menu': 'hidden',
     'name': 'Hidden',
     'hidden': True},
]

INTERNAL_IPS = ['127.0.0.1/8']
TRACKMAN_URL = "http://localhost:9090/"

MAIL_FROM = "noreply@localhost"
SMTP_SERVER = "mailhog"
SMTP_PORT = 1025
SMTP_TLS = False
SMTP_USER = ""
SMTP_PASSWORD = ""
DONATE_MAIL_FROM = "donations@localhost"

PROXY_FIX = False
PROXY_FIX_NUM_PROXIES = 1

MIN_PASSWORD_LENGTH = 8

UPLOAD_DIR = "/data/media"

DONATE_ENABLE = False
STRIPE_NAME = ""
STRIPE_DESCRIPTION = ""
STRIPE_SECRET_KEY = ""
STRIPE_PUBLIC_KEY = ""
STRIPE_MISSIONCONTROL_EMAIL = ""

# Allow CSRF tokens to last for 31 days
WTF_CSRF_TIME_LIMIT = 2678400

AUTH_METHOD = 'local'
AUTH_SUPERADMINS = ['admin']
AUTH_ROLE_GROUPS = {
    'admin': ['webmasters'],
    'content': ['webmasters'],
    'business': ['business'],
    'library': ['librarians'],
    'missioncontrol': ['missioncontrol'],
}

SENTRY_DSN = ""
