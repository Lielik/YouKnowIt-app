# Represents the "decks" table — a deck belongs to a user and contains cards

from datetime import datetime, timezone

from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship

from app.database import Base


class Deck(Base):
    __tablename__ = "decks"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"),
                     nullable=False)  # owner of the deck
    name = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    owner = relationship("User", back_populates="decks")
    # deleting a deck also deletes all its cards
    cards = relationship("Card", back_populates="deck",
                         cascade="all, delete-orphan")
    session_decks = relationship("SessionDeck", back_populates="deck")
