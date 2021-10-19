import config
from sqlalchemy import Column, Integer, String, Boolean, Float, DateTime, ForeignKey
from sqlalchemy.orm import relationship

class db_User(config.TBase):

    __tablename__ = 'db_users'

    id = Column(Integer, primary_key=True)
    phone_number = Column(String)
    name = Column(String(32))
    is_chef = Column(Boolean)
    password = Column(String)
    reg_date = Column(DateTime)


class Meal(config.TBase):

    __tablename__ = 'meals'

    id = Column(Integer, primary_key=True, autoincrement=True)
    img = Column(String)
    name = Column(String, unique=True)
    cost = Column(Float)
    orders = relationship("Order", back_populates="meal")


class Order(config.TBase):

    __tablename__ = 'orders'

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey('db_users.id'))
    contact_phone_number = Column(String)
    content = Column(String, ForeignKey('meals.name'))
    status = Column(String)
    ins_date = Column(DateTime)
    meal = relationship("Meal", back_populates="orders")
