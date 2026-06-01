# Unit tests for Pydantic schema validation — no database needed

import pytest
from pydantic import ValidationError

from app.schemas.auth import UserRegister, UserLogin
from app.schemas.deck import DeckCreate, DeckUpdate
from app.schemas.card import CardCreate, CardProgressUpdate
from app.models.progress import CardStatus


def test_user_register_valid():
    user = UserRegister(
        username="john", email="john@example.com", password="pass123")
    assert user.username == "john"
    assert user.email == "john@example.com"


def test_user_register_invalid_email():
    with pytest.raises(ValidationError):
        UserRegister(username="john", email="notanemail", password="pass123")


def test_user_login_valid():
    login = UserLogin(email="john@example.com", password="pass123")
    assert login.email == "john@example.com"


def test_deck_create_valid():
    deck = DeckCreate(name="Python", description="Python basics")
    assert deck.name == "Python"


def test_deck_create_no_description():
    deck = DeckCreate(name="Python")
    assert deck.description is None


def test_deck_update_partial():
    # All fields optional — can update just name
    update = DeckUpdate(name="New Name")
    assert update.name == "New Name"
    assert update.description is None


def test_card_create_valid():
    card = CardCreate(question="What is Docker?",
                      answer="A containerization platform")
    assert card.question == "What is Docker?"


def test_card_progress_valid_status():
    progress = CardProgressUpdate(status=CardStatus.I_KNOW_THIS)
    assert progress.status == CardStatus.I_KNOW_THIS


def test_card_progress_invalid_status():
    with pytest.raises(ValidationError):
        CardProgressUpdate(status="invalid_status")
