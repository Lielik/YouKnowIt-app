# Handles statistics endpoints for the statistics page

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_user
from app.database import get_db
from app.models.card import Card
from app.models.deck import Deck
from app.models.progress import CardProgress, CardStatus
from app.models.session import StudySession, SessionStatus
from app.models.user import User
from app.schemas.stats import DeckStats, OverallStats

router = APIRouter(prefix="/api/stats", tags=["stats"])


def build_deck_stats(deck: Deck, user_id: int, db: Session) -> DeckStats:
    # Helper that calculates known/unknown stats for a single deck
    total = len(deck.cards)
    known = db.query(CardProgress).filter(
        CardProgress.user_id == user_id,
        CardProgress.card_id.in_([c.id for c in deck.cards]),
        CardProgress.status == CardStatus.I_KNOW_THIS,
    ).count()

    unknown = total - known
    # avoid division by zero for empty decks
    known_percentage = round((known / total) * 100, 1) if total > 0 else 0.0

    return DeckStats(
        deck_id=deck.id,
        deck_name=deck.name,
        total_cards=total,
        known_cards=known,
        unknown_cards=unknown,
        known_percentage=known_percentage,
    )


@router.get("", response_model=OverallStats)
def get_overall_stats(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    # Fetch all user's decks and sessions
    decks = db.query(Deck).filter(Deck.user_id == current_user.id).all()
    all_card_ids = [card.id for deck in decks for card in deck.cards]

    # Session counts
    total_sessions = db.query(StudySession).filter(
        StudySession.user_id == current_user.id
    ).count()

    completed_sessions = db.query(StudySession).filter(
        StudySession.user_id == current_user.id,
        StudySession.status == SessionStatus.COMPLETED,
    ).count()

    paused_sessions = db.query(StudySession).filter(
        StudySession.user_id == current_user.id,
        StudySession.status == SessionStatus.PAUSED,
    ).count()

    # Total card reviews across all sessions
    from app.models.session import SessionReview
    total_cards_reviewed = db.query(SessionReview).join(StudySession).filter(
        StudySession.user_id == current_user.id
    ).count()

    # Overall known/unknown counts across all decks
    total_cards = len(all_card_ids)
    known_cards = db.query(CardProgress).filter(
        CardProgress.user_id == current_user.id,
        CardProgress.card_id.in_(all_card_ids),
        CardProgress.status == CardStatus.I_KNOW_THIS,
    ).count() if all_card_ids else 0

    unknown_cards = total_cards - known_cards
    known_percentage = round((known_cards / total_cards)
                             * 100, 1) if total_cards > 0 else 0.0

    # Build per-deck stats for the pie chart
    deck_stats = [build_deck_stats(deck, current_user.id, db)
                  for deck in decks]

    return OverallStats(
        total_sessions=total_sessions,
        completed_sessions=completed_sessions,
        paused_sessions=paused_sessions,
        total_cards_reviewed=total_cards_reviewed,
        total_decks=len(decks),
        total_cards=total_cards,
        known_cards=known_cards,
        unknown_cards=unknown_cards,
        known_percentage=known_percentage,
        deck_stats=deck_stats,
    )


@router.get("/decks/{deck_id}", response_model=DeckStats)
def get_deck_stats(
    deck_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    # Returns stats for a specific deck
    deck = db.query(Deck).filter(
        Deck.id == deck_id,
        Deck.user_id == current_user.id,
    ).first()
    if not deck:
        raise HTTPException(status_code=404, detail="Deck not found")

    return build_deck_stats(deck, current_user.id, db)
