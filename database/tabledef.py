import config
from sqlalchemy import Column, Integer, String, Boolean, Float, DateTime, ForeignKey, create_engine
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()
engine = create_engine(config.DATABASE, echo=False)


class db_User(Base):

    __tablename__ = 'db_users'

    id = Column(Integer, primary_key=True)
    phone_number = Column(String)
    name = Column(String(32))
    is_chef = Column(Boolean)
    password = Column(String)
    reg_date = Column(DateTime)

    # def __init__(self, id, phone_number, name, is_chef, password, reg_date):
    #     self.id = id
    #     self.phone_number = phone_number
    #     self.name = name
    #     self.is_chef = is_chef
    #     self.password = password
    #     self.reg_date = reg_date


class Meal(Base):

    __tablename__ = 'meals'

    id = Column(Integer, primary_key=True, autoincrement=True)
    img = Column(String)
    name = Column(String, unique=True)
    cost = Column(Float)
    orders = relationship("Order", back_populates="meal")

    # def __init__(self, id, img, name, desc, cost, ins_date):
    #     self.id = id
    #     self.img = img
    #     self.name = name
    #     self.desc = desc
    #     self.cost = cost
    #     self.ins_date = ins_date


class Order(Base):

    __tablename__ = 'orders'

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey('db_users.id'))
    contact_phone_number = Column(String)
    content = Column(String, ForeignKey('meals.name'))
    status = Column(String)
    ins_date = Column(DateTime)
    meal = relationship("Meal", back_populates="orders")

    # def __init__(self, id, user_id, contact_phone_number, content, status, ins_date):
    #     self.id = id
    #     self.user_id = user_id
    #     self.contact_phone_number = contact_phone_number
    #     self.content = content
    #     self.status = status
    #     self.ins_date = ins_date


Base.metadata.create_all(engine)
