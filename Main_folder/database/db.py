# database/db.py

from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

# SQLite DB file
DATABASE_URL = "sqlite:///mvjit_local.db"

# Engine = connection to the DB
engine = create_engine(
    DATABASE_URL,
    echo=False,   # set True if you want to see SQL queries
    future=True
)

# Base class for all ORM models
Base = declarative_base()

# Session factory (used to talk to DB)
SessionLocal = sessionmaker(
    bind=engine,
    autoflush=False,
    autocommit=False,
    future=True
)


def init_db():
    """
    Import models and create all tables in the DB.
    Call this once at startup or via init_db.py.
    """
    # Import models so that they register with Base.metadata
    from . import models  # noqa: F401

    Base.metadata.create_all(bind=engine)
