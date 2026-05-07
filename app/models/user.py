# Represents the "users" table in the database

from datetime import datetime, timezone

from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.orm import relationship

from app.database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, nullable=False, index=True)
    email = Column(String, unique=True, nullable=False, index=True)
    # never store plain text passwords
    password_hash = Column(String, nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    # cascade="all, delete-orphan" means deleting a user also deletes all their data
    decks = relationship("Deck", back_populates="owner",
                         cascade="all, delete-orphan")
    progress = relationship(
        "CardProgress", back_populates="user", cascade="all, delete-orphan")
    sessions = relationship(
        "StudySession", back_populates="user", cascade="all, delete-orphan")
