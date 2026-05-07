# Handles all deck operations — create, read, update, delete

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_user
from app.database import get_db
from app.models.card import Card
from app.models.deck import Deck
from app.models.progress import CardProgress, CardStatus
from app.models.user import User
from app.schemas.deck import DeckCreate, DeckResponse, DeckUpdate

router = APIRouter(prefix="/api/decks", tags=["decks"])


def build_deck_response(deck: Deck, user_id: int, db: Session) -> DeckResponse:
    # Helper that calculates card statistics for a deck
    total = len(deck.cards)
    known = db.query(CardProgress).filter(
        CardProgress.user_id == user_id,
        CardProgress.card_id.in_([c.id for c in deck.cards]),
        CardProgress.status == CardStatus.I_KNOW_THIS,
    ).count()

    return DeckResponse(
        id=deck.id,
        name=deck.name,
        description=deck.description,
        created_at=deck.created_at,
        total_cards=total,
        known_cards=known,
        unknown_cards=total - known,
    )


@router.get("", response_model=list[DeckResponse])
def get_decks(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    # Returns all decks belonging to the logged-in user
    decks = db.query(Deck).filter(Deck.user_id == current_user.id).all()
    return [build_deck_response(deck, current_user.id, db) for deck in decks]


@router.post("", response_model=DeckResponse, status_code=status.HTTP_201_CREATED)
def create_deck(
    deck_data: DeckCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    deck = Deck(
        user_id=current_user.id,
        name=deck_data.name,
        description=deck_data.description,
    )
    db.add(deck)
    db.commit()
    db.refresh(deck)
    return build_deck_response(deck, current_user.id, db)


@router.get("/{deck_id}", response_model=DeckResponse)
def get_deck(
    deck_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    deck = db.query(Deck).filter(Deck.id == deck_id,
                                 Deck.user_id == current_user.id).first()
    if not deck:
        raise HTTPException(status_code=404, detail="Deck not found")
    return build_deck_response(deck, current_user.id, db)


@router.put("/{deck_id}", response_model=DeckResponse)
def update_deck(
    deck_id: int,
    deck_data: DeckUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    deck = db.query(Deck).filter(Deck.id == deck_id,
                                 Deck.user_id == current_user.id).first()
    if not deck:
        raise HTTPException(status_code=404, detail="Deck not found")

    # Only update fields that were actually provided
    if deck_data.name is not None:
        deck.name = deck_data.name
    if deck_data.description is not None:
        deck.description = deck_data.description

    db.commit()
    db.refresh(deck)
    return build_deck_response(deck, current_user.id, db)


@router.delete("/{deck_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_deck(
    deck_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    deck = db.query(Deck).filter(Deck.id == deck_id,
                                 Deck.user_id == current_user.id).first()
    if not deck:
        raise HTTPException(status_code=404, detail="Deck not found")

    db.delete(deck)
    db.commit()
    # 204 means "success, no content to return"
