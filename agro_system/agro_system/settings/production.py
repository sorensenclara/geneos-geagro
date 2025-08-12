import environ
from .base import *  # noqa

env = environ.Env(
    HOST=(str, None),
    URL_FRONT=(str, None),
)
env.read_env(f'{BASE_DIR}/../.env')  # noqa

HOST = env('HOST')
URL_FRONT = env('URL_FRONT')

ALLOWED_HOSTS = [HOST, URL_FRONT]
DEBUG = False