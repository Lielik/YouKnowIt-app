# Data structures for card endpoints

from datetime import datetime
from typing import Optional

from pydantic import BaseModel

from app.models.progress import CardStatus


class CardCreate(BaseModel):
    # Required fields when adding a new card to a deck
    question: str
    answer: str


class CardUpdate(BaseModel):
    # All fields optional — user can update just the question, just the answer, or both
    question: Optional[str] = None
    answer: Optional[str] = None


class CardResponse(BaseModel):
    # What we send back when returning a card
    id: int
    deck_id: int
    question: str
    answer: str
    created_at: datetime
    # The user's current knowledge status for this card
    # None means no progress record exists yet — treated as "i_will_know_this"
    status: Optional[CardStatus] = CardStatus.I_WILL_KNOW_THIS

    class Config:
        from_attributes = True


class CardProgressUpdate(BaseModel):
    # Used when the user flips a card and marks their status
    status: CardStatus
