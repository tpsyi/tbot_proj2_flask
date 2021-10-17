import os
from dotenv import load_dotenv
load_dotenv('vars.env')
from sqlalchemy.orm import declarative_base

CURRENCY = "UZS"        # Currency, used for payments and to describe prices
CUR_DEC = 100           # I use this because documentation said so ok? "price * 100 so as to include 2 decimal points"
MAX_ORDERS = 30         # Maximum orders one particular person can have in db at the same time.

ORDERS_LOG = os.environ.get("ORDERS_LOG", "log/orders_log.txt")  # Where to store log file, contains rejected  and completed orders
DATABASE = os.environ.get("DATABASE", "sqlite:///database//tbot.db")  # Default database location
APP_DATABASE = os.environ.get("APP_DATABASE", "sqlite:///app_dir//database//app.db") # Default database location for web interface
Base = declarative_base()

TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
PAYMENT_TOKEN = os.environ.get("PAYMENT_TOKEN")