import config
from sqlalchemy import Column, String, Integer, Boolean, DateTime

class web_admin(config.Base):
    __tablename__ = 'web_admins'

    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String(32), unique=True)
    password = Column(String(32))
    active = Column(Boolean)
    reg_date = Column(DateTime)