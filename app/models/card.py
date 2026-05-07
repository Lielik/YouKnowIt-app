# Represents the "cards" table — a card belongs to a deck and has a question and answer

from datetime import datetime, timezone

from sqlalchemy import Column, Integer, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship

from app.database import Base


class Card(Base):
    __tablename__ = "cards"

    id = Column(Integer, primary_key=True, index=True)
    # which deck this card belongs to
    deck_id = Column(Integer, ForeignKey("decks.id"), nullable=False)
    question = Column(Text, nullable=False)  # front of the card
    answer = Column(Text, nullable=False)    # back of the card
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    deck = relationship("Deck", back_populates="cards")
    # deleting a card also deletes its progress records and review history
    progress = relationship(
        "CardProgress", back_populates="card", cascade="all, delete-orphan")
    reviews = relationship("SessionReview", back_populates="card")
