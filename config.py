import re

TOKEN = '6887191350:AAE5bRQoDsqaqWDkjKk6vL4v0DLQ35lvw6g'
KEY_CIPHER = b'6266e90bd2a4e6ea1d30c5a7e8c6c18b'
COUNT_OWNER = 1
CALLBACK_PATTERN_LEFT = re.compile(r'<--:(.*)$')
CALLBACK_PATTERN_RIGHT = re.compile(r'-->:(.*)$')
CALLBACK_PATTERN_SUBSCRIBE = re.compile(r'^(.*):subscribe$')
CALLBACK_PATTERN_UNSUBSCRIBE = re.compile(r'^(.*):unsubscribe$')
PATTERN_PROFILE_VIEW = re.compile(r'анкета\s+@?[a-zA-Z0-9_]{5,32}$', re.IGNORECASE)
MAP_LINK_PATTERN = re.compile(r'https?://.*(maps|map|geo|earth|osm)/.*', re.IGNORECASE)
WORKER_STATUS = ['Начинающий', 'Маршал', 'Основной состав']
OWNER_STATUS = ['Владелец']
