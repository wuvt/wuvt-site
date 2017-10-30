DEBUG = False
# SESSION_COOKIE_SECURE = True

SQLALCHEMY_TRACK_MODIFICATIONS = False
REDIS_URL = 'redis://localhost:6379/0'

POSTS_PER_PAGE = 5
ARTISTS_PER_PAGE = 500
SANITIZE_SUMMARY = True

STATION_NAME = "WUVT-FM 90.7 Blacksburg, VA"
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

# DJ activity timer for automation/DJ logout in seconds
DJ_TIMEOUT = 30 * 60
EXTENDED_DJ_TIMEOUT = 120 * 60
NO_DJ_TIMEOUT = 5 * 60

CELERY_BROKER_URL = REDIS_URL
CELERY_RESULT_BACKEND = REDIS_URL
CELERY_TIMEZONE = 'America/New_York'
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'

AUTOMATION_PASSWORD = ""
ICECAST_URL = ""
ICECAST_MOUNTS = []
INTERNAL_IPS = ['127.0.0.1/8']
TRACKMAN_NAME = "Trackman"
TRACKMAN_ARTIST_PROHIBITED = ["?", "-"]
TRACKMAN_LABEL_PROHIBITED = ["?", "-", "same"]
TRACKMAN_DJ_HIDE_AFTER_DAYS = 425

ARCHIVE_URL_FORMAT = ""
MUSICBRAINZ_HOSTNAME = "musicbrainz.org"
MUSICBRAINZ_RATE_LIMIT = 1.0

ADMINS = []
MAIL_FROM = "noreply@localhost"
SMTP_SERVER = "localhost"
CHART_MAIL = False
CHART_MAIL_DEST = "charts@localhost"
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
