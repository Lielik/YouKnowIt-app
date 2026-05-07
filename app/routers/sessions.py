# Handles study session operations — start, pause, resume, end, and card reviews

import random
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_user
from app.database import get_db
from app.models.card import Card
from app.models.deck import Deck
from app.models.progress import CardProgress, CardStatus
from app.models.session import SessionStatus, StudySession, SessionDeck, SessionReview
from app.models.user import User
from app.schemas.session import (
    SessionCreate,
    SessionResponse,
    SessionCardResponse,
    SessionReviewCreate,
)

router = APIRouter(prefix="/api/sessions", tags=["sessions"])


def build_session_response(session: StudySession, db: Session) -> SessionResponse:
    # Helper that calculates session progress stats
    deck_ids = [sd.deck_id for sd in session.session_decks]
    total_cards = db.query(Card).filter(Card.deck_id.in_(deck_ids)).count()
    reviewed_cards = db.query(SessionReview).filter(
        SessionReview.session_id == session.id
    ).count()

    return SessionResponse(
        id=session.id,
        status=session.status,
        started_at=session.started_at,
        paused_at=session.paused_at,
        ended_at=session.ended_at,
        deck_ids=deck_ids,
        total_cards=total_cards,
        reviewed_cards=reviewed_cards,
    )


@router.post("", response_model=SessionResponse, status_code=status.HTTP_201_CREATED)
def start_session(
    session_data: SessionCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    # Verify all requested decks exist and belong to the current user
    for deck_id in session_data.deck_ids:
        deck = db.query(Deck).filter(
            Deck.id == deck_id,
            Deck.user_id == current_user.id,
        ).first()
        if not deck:
            raise HTTPException(
                status_code=404, detail=f"Deck {deck_id} not found")

    # Create the session
    session = StudySession(user_id=current_user.id)
    db.add(session)
    db.flush()  # flush to get the session id before adding related records

    # Link the chosen decks to this session
    for deck_id in session_data.deck_ids:
        db.add(SessionDeck(session_id=session.id, deck_id=deck_id))

    db.commit()
    db.refresh(session)
    return build_session_response(session, db)


@router.get("/paused", response_model=list[SessionResponse])
def get_paused_sessions(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    # Returns all paused sessions so the user can choose to resume one
    sessions = db.query(StudySession).filter(
        StudySession.user_id == current_user.id,
        StudySession.status == SessionStatus.PAUSED,
    ).all()
    return [build_session_response(s, db) for s in sessions]


@router.get("/{session_id}", response_model=SessionResponse)
def get_session(
    session_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    session = db.query(StudySession).filter(
        StudySession.id == session_id,
        StudySession.user_id == current_user.id,
    ).first()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    return build_session_response(session, db)


@router.get("/{session_id}/next-card", response_model=SessionCardResponse)
def get_next_card(
    session_id: int,
    only_unknown: bool = False,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    session = db.query(StudySession).filter(
        StudySession.id == session_id,
        StudySession.user_id == current_user.id,
        StudySession.status == SessionStatus.IN_PROGRESS,
    ).first()
    if not session:
        raise HTTPException(status_code=404, detail="Active session not found")

    # Get all cards from the session's decks
    deck_ids = [sd.deck_id for sd in session.session_decks]
    cards_query = db.query(Card).filter(Card.deck_id.in_(deck_ids))

    if only_unknown:
        # Filter to only cards marked "i_will_know_this"
        known_card_ids = db.query(CardProgress.card_id).filter(
            CardProgress.user_id == current_user.id,
            CardProgress.status == CardStatus.I_KNOW_THIS,
        ).subquery()
        cards_query = cards_query.filter(Card.id.not_in(known_card_ids))

    # Exclude cards already reviewed in this session
    reviewed_card_ids = db.query(SessionReview.card_id).filter(
        SessionReview.session_id == session_id
    ).subquery()
    cards_query = cards_query.filter(Card.id.not_in(reviewed_card_ids))

    remaining_cards = cards_query.all()

    if not remaining_cards:
        raise HTTPException(status_code=404, detail="No more cards to review")

    # Pick a random card from the remaining ones
    card = random.choice(remaining_cards)

    progress = db.query(CardProgress).filter(
        CardProgress.card_id == card.id,
        CardProgress.user_id == current_user.id,
    ).first()

    return SessionCardResponse(
        id=card.id,
        question=card.question,
        answer=card.answer,
        deck_id=card.deck_id,
        deck_name=card.deck.name,
        current_status=progress.status if progress else CardStatus.I_WILL_KNOW_THIS,
    )


@router.post("/{session_id}/review", status_code=status.HTTP_201_CREATED)
def review_card(
    session_id: int,
    review_data: SessionReviewCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    session = db.query(StudySession).filter(
        StudySession.id == session_id,
        StudySession.user_id == current_user.id,
        StudySession.status == SessionStatus.IN_PROGRESS,
    ).first()
    if not session:
        raise HTTPException(status_code=404, detail="Active session not found")

    # Record the review
    db.add(SessionReview(
        session_id=session_id,
        card_id=review_data.card_id,
        marked_as=review_data.marked_as,
    ))

    # Also update the card's overall progress
    progress = db.query(CardProgress).filter(
        CardProgress.card_id == review_data.card_id,
        CardProgress.user_id == current_user.id,
    ).first()

    if progress:
        progress.status = review_data.marked_as
    else:
        db.add(CardProgress(
            user_id=current_user.id,
            card_id=review_data.card_id,
            status=review_data.marked_as,
        ))

    db.commit()
    return {"message": "Review recorded"}


@router.patch("/{session_id}/pause")
def pause_session(
    session_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    session = db.query(StudySession).filter(
        StudySession.id == session_id,
        StudySession.user_id == current_user.id,
        StudySession.status == SessionStatus.IN_PROGRESS,
    ).first()
    if not session:
        raise HTTPException(status_code=404, detail="Active session not found")

    session.status = SessionStatus.PAUSED
    session.paused_at = datetime.now(timezone.utc)
    db.commit()
    return {"message": "Session paused"}


@router.patch("/{session_id}/resume")
def resume_session(
    session_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    session = db.query(StudySession).filter(
        StudySession.id == session_id,
        StudySession.user_id == current_user.id,
        StudySession.status == SessionStatus.PAUSED,
    ).first()
    if not session:
        raise HTTPException(status_code=404, detail="Paused session not found")

    session.status = SessionStatus.IN_PROGRESS
    session.paused_at = None  # clear the paused timestamp
    db.commit()
    return {"message": "Session resumed"}


@router.patch("/{session_id}/end")
def end_session(
    session_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    session = db.query(StudySession).filter(
        StudySession.id == session_id,
        StudySession.user_id == current_user.id,
        StudySession.status.in_(
            [SessionStatus.IN_PROGRESS, SessionStatus.PAUSED]),
    ).first()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    session.status = SessionStatus.COMPLETED
    session.ended_at = datetime.now(timezone.utc)
    db.commit()
    return {"message": "Session completed"}
