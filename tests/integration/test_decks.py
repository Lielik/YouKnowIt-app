# Tests for deck endpoints

def test_create_deck(authenticated_client):
    res = authenticated_client.post("/api/decks", json={
        "name": "Python",
        "description": "Python basics",
    })
    assert res.status_code == 201
    assert res.json()["name"] == "Python"
    assert res.json()["total_cards"] == 0


def test_create_deck_no_description(authenticated_client):
    res = authenticated_client.post("/api/decks", json={"name": "Math"})
    assert res.status_code == 201
    assert res.json()["description"] is None


def test_get_decks(authenticated_client):
    authenticated_client.post("/api/decks", json={"name": "Deck 1"})
    authenticated_client.post("/api/decks", json={"name": "Deck 2"})
    res = authenticated_client.get("/api/decks")
    assert res.status_code == 200
    assert len(res.json()) >= 2


def test_get_deck(authenticated_client):
    create_res = authenticated_client.post(
        "/api/decks", json={"name": "Docker"})
    deck_id = create_res.json()["id"]
    res = authenticated_client.get(f"/api/decks/{deck_id}")
    assert res.status_code == 200
    assert res.json()["name"] == "Docker"


def test_get_deck_not_found(authenticated_client):
    res = authenticated_client.get("/api/decks/99999")
    assert res.status_code == 404


def test_update_deck(authenticated_client):
    create_res = authenticated_client.post(
        "/api/decks", json={"name": "Old Name"})
    deck_id = create_res.json()["id"]
    res = authenticated_client.put(
        f"/api/decks/{deck_id}", json={"name": "New Name"})
    assert res.status_code == 200
    assert res.json()["name"] == "New Name"


def test_delete_deck(authenticated_client):
    create_res = authenticated_client.post(
        "/api/decks", json={"name": "To Delete"})
    deck_id = create_res.json()["id"]
    res = authenticated_client.delete(f"/api/decks/{deck_id}")
    assert res.status_code == 204
    # Verify it's gone
    get_res = authenticated_client.get(f"/api/decks/{deck_id}")
    assert get_res.status_code == 404


def test_cannot_access_other_users_deck(client, authenticated_client):
    # Create a deck as user 1
    create_res = authenticated_client.post(
        "/api/decks", json={"name": "Private"})
    deck_id = create_res.json()["id"]

    # Register and login as user 2
    client.post("/api/auth/register", json={
        "username": "user2",
        "email": "user2@example.com",
        "password": "password123",
    })
    client.post("/api/auth/login", json={
        "email": "user2@example.com",
        "password": "password123",
    })

    # User 2 should not be able to access user 1's deck
    res = client.get(f"/api/decks/{deck_id}")
    assert res.status_code == 404
