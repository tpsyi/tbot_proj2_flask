from database import db_util
from database.tabledef import Meal
import datetime
import logging

datetime = datetime.datetime
ins_meals = []


""" Add meals through this file. You can also add them through the bot itself when in "chef" mode.
:Example:
ins_meals.append(Meal(
                  img='assets/meals/fried-egg-with-guacamole-sandwiches.jpg',     <==path to an image from root
                  name='Fried egg with Guacamole sandwiches',                     <==name of your meal, should be unique
                  cost=1000))                                    <== cost of the meal in currency specified in config.py
"""

ins_meals.append(Meal(
                  img='assets/meals/fried-egg-with-guacamole-sandwiches.jpg',
                  name='Fried egg with Guacamole sandwiches',
                  cost=1000))
ins_meals.append(Meal(
                  img='assets/meals/pancakes-with-walnuts.jpg',
                  name='Pancakes with walnuts',
                  cost=1100))
ins_meals.append(Meal(
                  img='assets/meals/pizza.jpg',
                  name='Pizza',
                  cost=1200))
ins_meals.append(Meal(
                  img='assets/meals/pumpkin-soup.jpg',
                  name='Pumpkin Soup',
                  cost=1300))
ins_meals.append(Meal(
                  img='assets/meals/shakshuka.jpg',
                  name='Shakshuka',
                  cost=1400))
ins_meals.append(Meal(
                  img='assets/meals/strawberry-cake.jpg',
                  name='Strawberry Cake',
                  cost=1500))
ins_meals.append(Meal(
                  img='assets/meals/tacos.jpg',
                  name='Tacos',
                  cost=1600))

def clear_meal_db():
    local_session = db_util.Session()
    for i in local_session.query(Meal).all():
        """Delete all elements of Meal table"""
        local_session.delete(i)
    local_session.close()

def insert():
    local_session = db_util.Session()
    if len(local_session.query(Meal).filter(Meal.name != ins_meals[0].name).all()) == 0:
        print("!!!")
        for meal in ins_meals:
            local_session.add(meal)
        local_session.commit()
    elif local_session.query(Meal).filter(Meal.name == ins_meals[0].name).all():
        logging.info("Tried to insert meals that are already present in db")
    local_session.close()
