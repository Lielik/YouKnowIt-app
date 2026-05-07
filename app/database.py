# Sets up the database connection and session factory
# get_db() is injected into any route that needs to query the database

from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

from app.core.config import settings

# The engine is the actual connection to PostgreSQL
engine = create_engine(settings.DATABASE_URL)

# Each request gets its own session — changes aren't saved until commit()
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# All models inherit from this — tells SQLAlchemy they represent DB tables
Base = declarative_base()


def get_db():
    # Opens a session, hands it to the route, closes it when the request is done
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
