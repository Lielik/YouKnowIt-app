# Tests for card endpoints

import pytest


@pytest.fixture
def deck_with_client(authenticated_client):
    # Creates a deck and returns both the client and deck id
    res = authenticated_client.post("/api/decks", json={"name": "Test Deck"})
    return authenticated_client, res.json()["id"]


def test_create_card(deck_with_client):
    client, deck_id = deck_with_client
    res = client.post(f"/api/decks/{deck_id}/cards", json={
        "question": "What is Docker?",
        "answer": "A containerization platform",
    })
    assert res.status_code == 201
    assert res.json()["question"] == "What is Docker?"
    assert res.json()["answer"] == "A containerization platform"


def test_get_cards(deck_with_client):
    client, deck_id = deck_with_client
    client.post(f"/api/decks/{deck_id}/cards", json={
        "question": "Q1", "answer": "A1"
    })
    client.post(f"/api/decks/{deck_id}/cards", json={
        "question": "Q2", "answer": "A2"
    })
    res = client.get(f"/api/decks/{deck_id}/cards")
    assert res.status_code == 200
    assert len(res.json()) == 2


def test_update_card(deck_with_client):
    client, deck_id = deck_with_client
    create_res = client.post(f"/api/decks/{deck_id}/cards", json={
        "question": "Old Q", "answer": "Old A"
    })
    card_id = create_res.json()["id"]
    res = client.put(f"/api/cards/{card_id}", json={"question": "New Q"})
    assert res.status_code == 200
    assert res.json()["question"] == "New Q"
    assert res.json()["answer"] == "Old A"  # unchanged


def test_delete_card(deck_with_client):
    client, deck_id = deck_with_client
    create_res = client.post(f"/api/decks/{deck_id}/cards", json={
        "question": "Q", "answer": "A"
    })
    card_id = create_res.json()["id"]
    res = client.delete(f"/api/cards/{card_id}")
    assert res.status_code == 204


def test_update_card_progress(deck_with_client):
    client, deck_id = deck_with_client
    create_res = client.post(f"/api/decks/{deck_id}/cards", json={
        "question": "Q", "answer": "A"
    })
    card_id = create_res.json()["id"]

    # Default status should be i_will_know_this
    assert create_res.json()["status"] == "i_will_know_this"

    # Mark as known
    res = client.patch(f"/api/cards/{card_id}/progress", json={
        "status": "i_know_this"
    })
    assert res.status_code == 200
    assert res.json()["status"] == "i_know_this"

    # Toggle back
    res = client.patch(f"/api/cards/{card_id}/progress", json={
        "status": "i_will_know_this"
    })
    assert res.status_code == 200
    assert res.json()["status"] == "i_will_know_this"
