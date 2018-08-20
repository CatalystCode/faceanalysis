from os import environ
from os.path import abspath
from os.path import dirname

LOGGING_LEVEL = environ.get('LOGGING_LEVEL', 'WARNING')

MOUNTED_DATA_DIR = environ.get('MOUNTED_DATA_DIR')
HOST_DATA_DIR = environ.get('HOST_DATA_DIR')

IMAGE_PROCESSOR_CONCURRENCY = int(environ.get(
    'IMAGE_PROCESSOR_CONCURRENCY',
    '3'))
IMAGE_PROCESSOR_QUEUE = environ.get('IMAGE_PROCESSOR_QUEUE', 'faceanalysis')
CELERY_BROKER = 'pyamqp://{user}:{password}@{host}'.format(
    user=environ.get('RABBITMQ_USER', 'guest'),
    password=environ.get('RABBITMQ_PASSWORD', 'guest'),
    host=environ['RABBITMQ_HOST'])

ALLOWED_EXTENSIONS = set(
    environ.get('ALLOWED_IMAGE_FILE_EXTENSIONS', '')
    .lower().split('_')) - {''}

DISTANCE_SCORE_THRESHOLD = float(environ.get(
    'DISTANCE_SCORE_THRESHOLD',
    '0.6'))
FACE_VECTORIZE_ALGORITHM = environ.get(
    'FACE_VECTORIZE_ALGORITHM',
    'cwolff/face_recognition')

TOKEN_SECRET_KEY = environ.get('TOKEN_SECRET_KEY', '')
TOKEN_EXPIRATION = int(environ.get(
    'DEFAULT_TOKEN_EXPIRATION_SECS',
    '500'))

SQLALCHEMY_CONNECTION_STRING = (
    'mysql+mysqlconnector://{user}:{password}@{host}:3306/{database}'
    .format(user=environ['MYSQL_USER'],
            password=environ['MYSQL_PASSWORD'],
            host=environ['MYSQL_HOST'],
            database=environ['MYSQL_DATABASE']))

STORAGE_PROVIDER = environ.get('STORAGE_PROVIDER', 'LOCAL')
STORAGE_KEY = environ.get('STORAGE_KEY', dirname(abspath(__file__)))
STORAGE_SECRET = environ.get('STORAGE_SECRET', '')
STORAGE_CONTAINER = environ.get('STORAGE_CONTAINER', 'images')

DOCKER_DAEMON = environ.get('DOCKER_DAEMON', 'unix://var/run/docker.sock')

FACE_API_MODEL_ID = environ.get('FACE_API_MODEL_ID', '')
FACE_API_ACCESS_KEY = environ.get('FACE_API_ACCESS_KEY', '')
FACE_API_ENDPOINT = environ.get('FACE_API_ENDPOINT')
if not FACE_API_ENDPOINT and environ.get('FACE_API_REGION'):
    FACE_API_ENDPOINT = 'https://{region}.api.cognitive.microsoft.com'.format(
        region=environ.get('FACE_API_REGION', ''))
if FACE_API_ENDPOINT and not FACE_API_ENDPOINT.endswith('/face/v1.0/'):
    FACE_API_ENDPOINT += '/face/v1.0/'
