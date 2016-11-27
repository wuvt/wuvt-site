DEBUG = False
# SESSION_COOKIE_SECURE = True
CSRF_COOKIE_HTTPONLY = True
# CSRF_COOKIE_SECURE = True
CSRF_COOKIE_TIMEOUT = None

SQLALCHEMY_DATABASE_URI = 'sqlite:////usr/src/app/wuvt.db'
SQLALCHEMY_TRACK_MODIFICATIONS = False
REDIS_URL = 'redis://localhost:6379'

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
TRACKMAN_ARTIST_BLACKLIST = ["?"]
TRACKMAN_LABEL_BLACKLIST = ["same"]

ARCHIVE_URL_FORMAT= ""
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
LDAP_AUTH = False
LDAP_URI = 'ldap://127.0.0.1:389'
LDAP_VERIFY = True
LDAP_BASE_DN = "dc=wuvt,dc=vt,dc=edu"
LDAP_AUTH_DN = "uid={},ou=Users,dc=wuvt,dc=vt,dc=edu"
LDAP_GROUPS_ADMIN = ['sudoers', 'webmasters']
LDAP_GROUPS_BUSINESS = ['sudoers']
LDAP_GROUPS_LIBRARY = ['sudoers', 'librarians']
LDAP_GROUPS_RADIOTHON = ['sudoers', 'missioncontrol']

UPLOAD_DIR = "/data/media"

RADIOTHON = False

DONATE_ENABLE = False
STRIPE_NAME = ""
STRIPE_DESCRIPTION = ""
STRIPE_SECRET_KEY = ""
STRIPE_PUBLIC_KEY = ""
DONATE_PREMIUMS = False
DONATE_SHIPPING_MINIMUM = 10
DONATE_SHIPPING_COST = 6
DONATE_TSHIRTSIZES = ['S', 'M', 'L', 'XL', 'XXL']
DONATE_TSHIRTCOLORS = []
DONATE_SWEATSHIRTSIZES = DONATE_TSHIRTSIZES
