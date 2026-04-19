# Secure config using environment variables from .htaccess SetEnv
import os

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
DB_PATH = os.path.join(BASE_DIR, 'users.db')

SQLALCHEMY_DATABASE_URI = f'sqlite:///{DB_PATH}'
SQLALCHEMY_TRACK_MODIFICATIONS = False

# Try environment first, fallback to .htaccess SetEnv values
def get_env(name, default=''):
    return os.environ.get(name, default)

BOT_TOKEN = os.environ.get('BOT_TOKEN', '8716164046:AAGHHmqjUZKoOL_7bl1D6e4gyWkIcxSJKO4')
ADMIN_CHAT_ID = os.environ.get('ADMIN_CHAT_ID', '2114966435')
GROUP_CHAT_ID = os.environ.get('GROUP_CHAT_ID', '-1003669812066')
DOWNLOAD_URL = ''

SECRET_KEY = os.environ.get('SECRET_KEY', 'change-me-in-production')
ADMIN_PASSWORD = os.environ.get('ADMIN_PASSWORD', '05509054753f')

TRIBUTE_API_KEY = ''

SELECTEL_ACCESS_KEY = os.environ.get('SELECTEL_ACCESS_KEY', '2912482207e54fc2a1caea22df512978')
SELECTEL_SECRET_KEY = os.environ.get('SELECTEL_SECRET_KEY', '2305049c095b44ceb827f84a80076095')

KEY_LENGTH = 16
MAX_KEYS_PER_USER = 5
SESSION_TIMEOUT = 86400

KEY_TYPES = {
    'test': {'days': 1, 'price': 0},
    '30d': {'days': 30, 'price': 60000},
    '180d': {'days': 180, 'price': 300000},
    '365d': {'days': 365, 'price': 630000},
    'permanent': {'days': None, 'price': 1000000}
}

PRICES = {60000: '30d', 300000: '180d', 630000: '365d', 1000000: 'permanent'}
SUBSCRIPTION_NAMES = {'РўРµСЃС‚РѕРІС‹Р№ РґРѕСЃС‚СѓРї': 'test', 'РџРѕР»РіРѕРґР°': '180d', 'Р“РѕРґ': '365d', 'РќР°РІСЃРµРіРґР°': 'permanent'}