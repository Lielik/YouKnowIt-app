# Unit tests for security functions — no database needed

from app.core.security import hash_password, verify_password, create_access_token, decode_access_token


def test_hash_password_returns_hash():
    hashed = hash_password("mypassword")
    assert hashed != "mypassword"
    assert len(hashed) > 0


def test_verify_password_correct():
    hashed = hash_password("mypassword")
    assert verify_password("mypassword", hashed) is True


def test_verify_password_wrong():
    hashed = hash_password("mypassword")
    assert verify_password("wrongpassword", hashed) is False


def test_create_and_decode_token():
    token = create_access_token(data={"sub": "123"})
    payload = decode_access_token(token)
    assert payload is not None
    assert payload["sub"] == "123"


def test_decode_invalid_token():
    payload = decode_access_token("invalid.token.here")
    assert payload is None


def test_decode_tampered_token():
    token = create_access_token(data={"sub": "123"})
    tampered = token + "tampered"
    payload = decode_access_token(tampered)
    assert payload is None
