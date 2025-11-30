# database/models.py

from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.sql import func



from datetime import datetime
import pytz
from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.sql import func
from .db import Base

IST = pytz.timezone("Asia/Kolkata")

class VisitorLog(Base):
    __tablename__ = "visitor_logs"

    id = Column(Integer, primary_key=True, index=True)

    timestamp = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(IST),   # <<< HERE
        nullable=False
    )

    name = Column(String(100), nullable=False)
    purpose = Column(String(255), nullable=True)


class User(Base):
    """
    Simple user table for login.
    Only email + password (plain text for now, local only).
    """
    __tablename__ = "user"

    id = Column(Integer, primary_key=True, autoincrement=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    password = Column(String(255), nullable=False)