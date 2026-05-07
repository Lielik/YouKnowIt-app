# Data structures for deck endpoints
# Create/Update define what we accept, DeckResponse defines what we send back

from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class DeckCreate(BaseModel):
    # Required fields when creating a new deck
    name: str
    description: Optional[str] = None  # description is optional


class DeckUpdate(BaseModel):
    # All fields optional — user can update just the name, just the description, or both
    name: Optional[str] = None
    description: Optional[str] = None


class DeckResponse(BaseModel):
    # What we send back when returning a deck
    id: int
    name: str
    description: Optional[str]
    created_at: datetime
    total_cards: int = 0        # how many cards are in the deck
    known_cards: int = 0        # how many are marked "i_know_this"
    unknown_cards: int = 0      # how many are marked "i_will_know_this"

    class Config:
        from_attributes = True
