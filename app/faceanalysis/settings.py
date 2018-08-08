from os import environ
from os.path import abspath
from os.path import dirname

LOGGING_LEVEL = environ.get('LOGGING_LEVEL', 'WARNING')

MOUNTED_DATA_DIR = environ.get('MOUNTED_DATA_DIR')
HOST_DATA_DIR = environ.get('HOST_DATA_DIR')

STORAGE_ACCOUNT_NAME = environ['STORAGE_ACCOUNT_NAME']
STORAGE_ACCOUNT_KEY = environ['STORAGE_ACCOUNT_KEY']
IMAGE_PROCESSOR_QUEUE = environ.get('IMAGE_PROCESSOR_QUEUE', 'faceanalysis')

ALLOWED_EXTENSIONS = set(
    environ.get('ALLOWED_IMAGE_FILE_EXTENSIONS', '')
    .lower().split('_')) - {''}

DISTANCE_SCORE_THRESHOLD = float(environ.get(
    'DISTANCE_SCORE_THRESHOLD',
    '0.6'))
FACE_VECTORIZE_ALGORITHM = environ.get(
    'FACE_VECTORIZE_ALGORITHM',
    'cwolff/face_recognition')

TOKEN_SECRET_KEY = environ.get('TOKEN_SECRET_KEY')
TOKEN_EXPIRATION = int(environ.get(
    'DEFAULT_TOKEN_EXPIRATION_SECS',
    '500'))

MYSQL_USER = environ['MYSQL_USER']
MYSQL_PASSWORD = environ['MYSQL_PASSWORD']
MYSQL_HOST = environ['MYSQL_HOST']
MYSQL_DATABASE = environ['MYSQL_DATABASE']

STORAGE_PROVIDER = environ.get('STORAGE_PROVIDER', 'LOCAL')
STORAGE_KEY = environ.get('STORAGE_KEY', dirname(abspath(__file__)))
STORAGE_SECRET = environ.get('STORAGE_SECRET', '')
STORAGE_CONTAINER = environ.get('STORAGE_CONTAINER', 'images')
