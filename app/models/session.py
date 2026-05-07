# Three tables that together track a study session:
# StudySession — the session itself (start/end time)
# SessionDeck  — which decks were included in the session
# SessionReview — each individual card review that happened in the session

import enum
from datetime import datetime, timezone

from sqlalchemy import Column, Integer, DateTime, ForeignKey, Enum
from sqlalchemy.orm import relationship

from app.database import Base
# reuse the same enum — same two valid values
from app.models.progress import CardStatus


class SessionStatus(enum.Enum):
    IN_PROGRESS = "in_progress"   # actively reviewing
    PAUSED = "paused"             # stopped, can be resumed later
    COMPLETED = "completed"       # finished, ended_at is set


class StudySession(Base):
    __tablename__ = "study_sessions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    status = Column(Enum(SessionStatus), nullable=False,
                    default=SessionStatus.IN_PROGRESS)
    started_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    paused_at = Column(DateTime, nullable=True)   # set when user pauses
    # set when session is completed
    ended_at = Column(DateTime, nullable=True)

    user = relationship("User", back_populates="sessions")
    session_decks = relationship(
        "SessionDeck", back_populates="session", cascade="all, delete-orphan")
    reviews = relationship(
        "SessionReview", back_populates="session", cascade="all, delete-orphan")


class SessionDeck(Base):
    __tablename__ = "session_decks"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, ForeignKey(
        "study_sessions.id"), nullable=False)
    deck_id = Column(Integer, ForeignKey("decks.id"), nullable=False)

    session = relationship("StudySession", back_populates="session_decks")
    deck = relationship("Deck", back_populates="session_decks")


class SessionReview(Base):
    __tablename__ = "session_reviews"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, ForeignKey(
        "study_sessions.id"), nullable=False)
    card_id = Column(Integer, ForeignKey("cards.id"), nullable=False)
    # reusing CardStatus enum — a review can only be marked as one of the two valid statuses
    marked_as = Column(Enum(CardStatus), nullable=False)
    reviewed_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    session = relationship("StudySession", back_populates="reviews")
    card = relationship("Card", back_populates="reviews")
