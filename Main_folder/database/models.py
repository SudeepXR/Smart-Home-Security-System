from sqlalchemy import (
    Column,
    Integer,
    String,
    DateTime,
    ForeignKey,
    LargeBinary
)
from sqlalchemy.orm import relationship
from datetime import datetime
from .db import Base


# =======================
# USERS TABLE
# =======================

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, nullable=False)   
    password_hash = Column(String, nullable=False)

    doorbell_ip = Column(String)
    cctv_ip = Column(String)

    file_destination = Column(String)  

    created_at = Column(DateTime, default=datetime.utcnow)

    visitor_logs = relationship(
        "VisitorLog",
        back_populates="user",
        cascade="all, delete"
    )


# =======================
# VISITOR LOGS TABLE
# =======================

class VisitorLog(Base):
    __tablename__ = "visitor_logs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    timestamp = Column(DateTime, default=datetime.utcnow)
    name = Column(String)
    purpose = Column(String)

    photo = Column(LargeBinary)  
    message_id = Column(String)    

    flag = Column(Integer, default=0)   

    user = relationship("User", back_populates="visitor_logs")
