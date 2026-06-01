# Tests for authentication endpoints

def test_register_success(client):
    res = client.post("/api/auth/register", json={
        "username": "newuser",
        "email": "new@example.com",
        "password": "password123",
    })
    assert res.status_code == 201
    assert res.json()["email"] == "new@example.com"
    assert "password_hash" not in res.json()


def test_register_duplicate_email(client, registered_user):
    res = client.post("/api/auth/register", json={
        "username": "anotheruser",
        "email": registered_user["email"],  # same email
        "password": "password123",
    })
    assert res.status_code == 400
    assert "Email already registered" in res.json()["detail"]


def test_register_duplicate_username(client, registered_user):
    res = client.post("/api/auth/register", json={
        "username": "testuser",  # same username
        "email": "different@example.com",
        "password": "password123",
    })
    assert res.status_code == 400
    assert "Username already taken" in res.json()["detail"]


def test_login_success(client, registered_user):
    res = client.post("/api/auth/login", json=registered_user)
    assert res.status_code == 200
    assert res.json()["message"] == "Login successful"
    # Cookie should be set
    assert "access_token" in res.cookies


def test_login_wrong_password(client, registered_user):
    res = client.post("/api/auth/login", json={
        "email": registered_user["email"],
        "password": "wrongpassword",
    })
    assert res.status_code == 401


def test_login_wrong_email(client):
    res = client.post("/api/auth/login", json={
        "email": "nobody@example.com",
        "password": "password123",
    })
    assert res.status_code == 401


def test_logout(authenticated_client):
    res = authenticated_client.post("/api/auth/logout")
    assert res.status_code == 200


def test_me(authenticated_client):
    res = authenticated_client.get("/api/auth/me")
    assert res.status_code == 200
    assert res.json()["email"] == "test@example.com"


def test_me_unauthenticated(client):
    res = client.get("/api/auth/me")
    assert res.status_code == 401
