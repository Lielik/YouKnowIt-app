# conftest.py — shared test fixtures available to all test files

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database import Base, get_db
from app.main import app

# Use a separate test database
TEST_DATABASE_URL = None  # loaded from environment variable in CI


@pytest.fixture(scope="session")
def engine():
    import os
    db_url = os.getenv("DATABASE_URL")
    engine = create_engine(db_url)
    # Create all tables once for the entire test session
    Base.metadata.create_all(bind=engine)
    yield engine
    # Drop all tables after all tests are done
    Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def db(engine):
    # Each test gets a fresh database session
    TestingSessionLocal = sessionmaker(bind=engine)
    session = TestingSessionLocal()
    yield session
    # Roll back any changes after each test — keeps tests isolated
    session.rollback()
    session.close()


@pytest.fixture(scope="function")
def client(db):
    # Override the get_db dependency to use the test database
    def override_get_db():
        yield db

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


@pytest.fixture
def registered_user(client):
    # Creates a test user and returns their credentials
    client.post("/api/auth/register", json={
        "username": "testuser",
        "email": "test@example.com",
        "password": "testpassword123",
    })
    return {"email": "test@example.com", "password": "testpassword123"}


@pytest.fixture
def authenticated_client(client, registered_user):
    # Returns a client that is already logged in
    client.post("/api/auth/login", json=registered_user)
    return client
