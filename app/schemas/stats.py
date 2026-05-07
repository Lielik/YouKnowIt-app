# Data structures for the statistics page

from typing import Optional, List

from pydantic import BaseModel


class DeckStats(BaseModel):
    # Statistics for a single deck
    deck_id: int
    deck_name: str
    total_cards: int
    known_cards: int        # marked "i_know_this"
    unknown_cards: int      # marked "i_will_know_this"
    known_percentage: float  # percentage of known cards out of total


class OverallStats(BaseModel):
    # Overall statistics across all decks
    total_sessions: int
    completed_sessions: int
    paused_sessions: int        # sessions that were paused and not yet resumed
    total_cards_reviewed: int   # total card reviews across all sessions
    total_decks: int
    total_cards: int
    known_cards: int
    unknown_cards: int
    known_percentage: float     # overall known percentage across all decks
    deck_stats: List[DeckStats]  # breakdown per deck — used for the pie chart
