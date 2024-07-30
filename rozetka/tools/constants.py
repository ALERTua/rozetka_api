import os
from collections import namedtuple

Setter = namedtuple('Setter', ['fnc', 'flds'])

VERBOSE = os.getenv('VERBOSE') in ('True', '1', 'true')

LANGUAGE = os.getenv('LANGUAGE', 'UA')
assert LANGUAGE, "Please fill the correct LANGUAGE variable"

COUNTRY = os.getenv('COUNTRY', 'UA')
assert COUNTRY, "Please fill the correct COUNTRY variable"

DEFAULT_HEADERS = {
    # 'Referer': 'https://rozetka.ua/',
    # 'User-Agent': USER_AGENT,
    # 'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
    # 'Accept-Encoding': 'gzip, deflate, br',
    # 'Accept-Language': 'uk,en-US;q=0.8,en;q=0.5,ru;q=0.3',
    # 'Connection': 'keep-alive',
}

DEFAULT_COOKIES = {
    'visitor_city': "1",
}
IMPERSONATE = os.getenv('IMPERSONATE', 'chrome120')
BULK_ITEMS_REQUEST_MAX_LENGTH = 60

THREADS_MAX = int(os.getenv('THREADS_MAX', 100))
CALLS_MAX = int(os.getenv('CALLS_MAX', 10))
CALLS_PERIOD = int(os.getenv('CALLS_PERIOD', 1))

GET_RETRY_DELAY_SEC = int(os.getenv('GET_RETRY_DELAY_SEC', 10))
GET_TIMEOUT = int(os.getenv('GET_TIMEOUT', 60))

INFLUXDB_URL = os.getenv('INFLUXDB_URL')
INFLUXDB_TOKEN = os.getenv('INFLUXDB_TOKEN')
INFLUXDB_ORG = os.getenv('INFLUXDB_ORG')
INFLUXDB_BUCKET = os.getenv('INFLUXDB_BUCKET')

TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')

DISCORD_WEBHOOK_URL = os.getenv('DISCORD_WEBHOOK_URL')

SLACK_WEBHOOK_URL = os.getenv('SLACK_WEBHOOK_URL')
SLACK_CHANNEL = os.getenv('SLACK_CHANNEL')
SLACK_USER_MENTIONS = os.getenv('SLACK_USER_MENTIONS', '')

TEAMS_WEBHOOK_URL = os.getenv('TEAMS_WEBHOOK_URL')
TEAMS_USER_MENTIONS = os.getenv('TEAMS_USER_MENTIONS', '')

MEASUREMENT = os.getenv('MEASUREMENT', 'goods')

DEFAULT_TAGS = [
    'id_',
]
TAGS = os.getenv('TAGS', DEFAULT_TAGS)
if isinstance(TAGS, str):
    TAGS = TAGS.split()

DEFAULT_FIELDS = [
    'price',
    'old_price',
    # 'stars',
    'discount',
    # 'comments_amount',
    # 'comments_mark',
]
FIELDS = os.getenv('FIELDS', DEFAULT_FIELDS)
if isinstance(FIELDS, str):
    FIELDS = FIELDS.split()
