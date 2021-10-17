from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from database.tabledef import Meal
import config
import datetime

engine = create_engine(config.DATABASE, echo=False)
Session = sessionmaker(bind=engine)
local_session = Session()
datetime = datetime.datetime

for i in local_session.query(Meal).all():
    """Delete all elements of Meal table"""
    local_session.delete(i)

""" Add meals through this file. You can also add them through the bot itself when in "chef" mode.
:Example:
local_session.add(Meal(
                  img='assets/meals/fried-egg-with-guacamole-sandwiches.jpg',     <==path to an image from root
                  name='Fried egg with Guacamole sandwiches',                     <==name of your meal, should be unique
                  cost=1000))                                    <== cost of the meal in currency specified in config.py
"""

local_session.add(Meal(
                  img='assets/meals/fried-egg-with-guacamole-sandwiches.jpg',
                  name='Fried egg with Guacamole sandwiches',
                  cost=1000))
local_session.add(Meal(
                  img='assets/meals/pancakes-with-walnuts.jpg',
                  name='Pancakes with walnuts',
                  cost=1100))
local_session.add(Meal(
                  img='assets/meals/pizza.jpg',
                  name='Pizza',
                  cost=1200))
local_session.add(Meal(
                  img='assets/meals/pumpkin-soup.jpg',
                  name='Pumpkin Soup',
                  cost=1300))
local_session.add(Meal(
                  img='assets/meals/shakshuka.jpg',
                  name='Shakshuka',
                  cost=1400))
local_session.add(Meal(
                  img='assets/meals/strawberry-cake.jpg',
                  name='Strawberry Cake',
                  cost=1500))
local_session.add(Meal(
                  img='assets/meals/tacos.jpg',
                  name='Tacos',
                  cost=1600))


local_session.commit()
