import os
from dotenv import load_dotenv
load_dotenv('vars.env')
from sqlalchemy.orm import declarative_base

CURRENCY = "UZS"        # Currency, used for payments and to describe prices
CUR_DEC = 100           # I use this because documentation said so ok? "price * 100 so as to include 2 decimal points"
MAX_ORDERS = 30         # Maximum orders one particular person can have in db at the same time.

# DEFAULT SETTING FOR ENVIRONMENT VARIABLES, SET THEM IN vars.env!!
# Where to store log file, contains rejected  and completed orders
ORDERS_LOG = os.environ.get("ORDERS_LOG", "log/orders_log.txt")
# Default database location
DATABASE = os.environ.get("DATABASE", "sqlite:///database//tbot.db")
# Default database location for web interface
APP_DATABASE = os.environ.get("APP_DATABASE", "sqlite:///app_dir//database//app.db")
# Generated salt length, required for password, recommended >= 16
SALT_LENGTH = int(os.environ.get("SALT_LENGTH", 8))
# Generated key length, required for password, recommended >= 64
KEY_LENGTH = int(os.environ.get("KEY_LENGTH", 8))
# Hash iteration count; the more the better, but also the slower. Recommended >=10000
ITERATION_COUNT = int(os.environ.get("ITERATION_COUNT", 100))

TBase = declarative_base()
WBase = declarative_base()

TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
PAYMENT_TOKEN = os.environ.get("PAYMENT_TOKEN")
