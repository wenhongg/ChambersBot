import os
import environ

root = environ.Path(__file__) - 2 # three folder back (/a/b/c/ - 3 = /)

env = environ.Env(DEBUG=(bool, False),)  # set default values and casting
environ.Env.read_env(root('.env'))  # reading .env file

DEBUG = env('DEBUG')
MASTER_CHAT_ID = env.str('MASTER_CHAT_ID')

OUTPUT_ID = env('OUTPUT_ID')
BOT_URL = env('BOT_URL')
PRODUCTION_MODE = env.bool('PRODUCTION_MODE', False)
HOST_URL = env('HOST_URL')
FRONT_URL = env('FRONT_URL')