import re

TOKEN = '<your token>'
KEY_CIPHER = b'<your encryption key>'
COUNT_OWNER = 1
CALLBACK_PATTERN_LEFT = re.compile(r'<--:(.*)$')
CALLBACK_PATTERN_RIGHT = re.compile(r'-->:(.*)$')
CALLBACK_PATTERN_SUBSCRIBE = re.compile(r'^(.*):subscribe$')
CALLBACK_PATTERN_UNSUBSCRIBE = re.compile(r'^(.*):unsubscribe$')
PATTERN_PROFILE_VIEW = re.compile(r'анкета\s+@?[a-zA-Z0-9_]{5,32}$', re.IGNORECASE)
MAP_LINK_PATTERN = re.compile(r'https?://.*(maps|map|geo|earth|osm)/.*', re.IGNORECASE)
WORKER_STATUS = ['Начинающий', 'Маршал', 'Основной состав']
OWNER_STATUS = ['Владелец']
