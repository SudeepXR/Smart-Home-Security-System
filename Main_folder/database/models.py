from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from .db import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, nullable=False)   # gmail id
    password_hash = Column(String, nullable=False)

    doorbell_ip = Column(String)
    cctv_ip = Column(String)

    file_destination = Column(String)  # redundant for now, future use

    created_at = Column(DateTime, default=datetime.utcnow)

    visitor_logs = relationship(
        "VisitorLog",
        back_populates="user",
        cascade="all, delete"
    )


class VisitorLog(Base):
    __tablename__ = "visitor_logs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    timestamp = Column(DateTime, default=datetime.utcnow)
    name = Column(String)
    purpose = Column(String)

    user = relationship("User", back_populates="visitor_logs")
