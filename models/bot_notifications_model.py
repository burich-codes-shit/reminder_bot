from backend.db import Base
from sqlalchemy import Column, ForeignKey, Integer, String, DateTime
from sqlalchemy.orm import relationship


class Notification(Base):
    __tablename__ = 'notifications'

    id = Column(Integer, primary_key=True, index=True)
    notification_text = Column(String)  # Переименуйте поле для ясности
    date = Column(DateTime)
    user_chat_id = Column(Integer, ForeignKey('users.chat_id'))  # Связь через chat_id

    user = relationship('User', back_populates='notifications')

