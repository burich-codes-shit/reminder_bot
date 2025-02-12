from backend.db import Base
from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import relationship


class User(Base):
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True, index=True)
    chat_id = Column(Integer, unique=True)  # Убедитесь, что chat_id уникален
    name = Column(String)
    first_name = Column(String, default=None)
    last_name = Column(String, default=None)
    username = Column(String, default=None)

    notifications = relationship('Notification', back_populates='user')

