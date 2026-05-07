# Data structures for study session endpoints

from datetime import datetime
from typing import Optional, List

from pydantic import BaseModel

from app.models.session import SessionStatus
from app.models.progress import CardStatus


class SessionCreate(BaseModel):
    # What we expect when starting a new session
    deck_ids: List[int]                    # which decks to include
    # if True, only review "i_will_know_this" cards
    only_unknown: bool = False


class SessionResponse(BaseModel):
    # What we send back about a session
    id: int
    status: SessionStatus
    started_at: datetime
    paused_at: Optional[datetime] = None
    ended_at: Optional[datetime] = None
    deck_ids: List[int] = []              # which decks are in this session
    total_cards: int = 0                  # total cards to review
    reviewed_cards: int = 0              # how many have been reviewed so far

    class Config:
        from_attributes = True


class SessionCardResponse(BaseModel):
    # A single card served during a review session
    id: int
    question: str
    answer: str
    deck_id: int
    deck_name: str                        # so the user knows which deck the card is from
    # the user's current knowledge status for this card
    current_status: CardStatus

    class Config:
        from_attributes = True


class SessionReviewCreate(BaseModel):
    # What we expect when the user marks a card during a session
    card_id: int
    marked_as: CardStatus
