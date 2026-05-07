# Handles all card operations — create, read, update, delete, and progress tracking

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_user
from app.database import get_db
from app.models.card import Card
from app.models.deck import Deck
from app.models.progress import CardProgress, CardStatus
from app.models.user import User
from app.schemas.card import CardCreate, CardProgressUpdate, CardResponse, CardUpdate

router = APIRouter(prefix="/api", tags=["cards"])


def build_card_response(card: Card, user_id: int, db: Session) -> CardResponse:
    # Helper that attaches the user's progress status to a card
    progress = db.query(CardProgress).filter(
        CardProgress.card_id == card.id,
        CardProgress.user_id == user_id,
    ).first()

    return CardResponse(
        id=card.id,
        deck_id=card.deck_id,
        question=card.question,
        answer=card.answer,
        created_at=card.created_at,
        # if no progress record exists yet, default to "i_will_know_this"
        status=progress.status if progress else CardStatus.I_WILL_KNOW_THIS,
    )


def get_deck_or_404(deck_id: int, user_id: int, db: Session) -> Deck:
    # Helper that fetches a deck and ensures it belongs to the current user
    deck = db.query(Deck).filter(Deck.id == deck_id,
                                 Deck.user_id == user_id).first()
    if not deck:
        raise HTTPException(status_code=404, detail="Deck not found")
    return deck


@router.get("/decks/{deck_id}/cards", response_model=list[CardResponse])
def get_cards(
    deck_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    # Returns all cards in a deck with the user's progress status for each
    deck = get_deck_or_404(deck_id, current_user.id, db)
    return [build_card_response(card, current_user.id, db) for card in deck.cards]


@router.post("/decks/{deck_id}/cards", response_model=CardResponse, status_code=status.HTTP_201_CREATED)
def create_card(
    deck_id: int,
    card_data: CardCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    get_deck_or_404(deck_id, current_user.id, db)

    card = Card(
        deck_id=deck_id,
        question=card_data.question,
        answer=card_data.answer,
    )
    db.add(card)
    db.commit()
    db.refresh(card)
    return build_card_response(card, current_user.id, db)


@router.put("/cards/{card_id}", response_model=CardResponse)
def update_card(
    card_id: int,
    card_data: CardUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    card = db.query(Card).join(Deck).filter(
        Card.id == card_id,
        Deck.user_id == current_user.id,  # ensure the card belongs to the current user
    ).first()
    if not card:
        raise HTTPException(status_code=404, detail="Card not found")

    if card_data.question is not None:
        card.question = card_data.question
    if card_data.answer is not None:
        card.answer = card_data.answer

    db.commit()
    db.refresh(card)
    return build_card_response(card, current_user.id, db)


@router.delete("/cards/{card_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_card(
    card_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    card = db.query(Card).join(Deck).filter(
        Card.id == card_id,
        Deck.user_id == current_user.id,
    ).first()
    if not card:
        raise HTTPException(status_code=404, detail="Card not found")

    db.delete(card)
    db.commit()


@router.patch("/cards/{card_id}/progress", response_model=CardResponse)
def update_progress(
    card_id: int,
    progress_data: CardProgressUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    # Verify the card exists and belongs to the current user
    card = db.query(Card).join(Deck).filter(
        Card.id == card_id,
        Deck.user_id == current_user.id,
    ).first()
    if not card:
        raise HTTPException(status_code=404, detail="Card not found")

    # Update existing progress record or create a new one
    progress = db.query(CardProgress).filter(
        CardProgress.card_id == card_id,
        CardProgress.user_id == current_user.id,
    ).first()

    if progress:
        progress.status = progress_data.status
    else:
        # First time marking this card — create a new progress record
        progress = CardProgress(
            user_id=current_user.id,
            card_id=card_id,
            status=progress_data.status,
        )
        db.add(progress)

    db.commit()
    db.refresh(card)
    return build_card_response(card, current_user.id, db)
