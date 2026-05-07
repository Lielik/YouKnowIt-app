# Structure for data coming in and going out of auth endpoints

from pydantic import BaseModel, EmailStr


class UserRegister(BaseModel):
    # Data we expect from the registration form
    username: str
    email: EmailStr  # EmailStr validates it's a real email format e.g. "user@example.com"
    password: str


class UserLogin(BaseModel):
    # Data we expect from the login form
    email: EmailStr
    password: str


class UserResponse(BaseModel):
    # What we send back about a user — password_hash is intentionally excluded
    id: int
    username: str
    email: EmailStr

    class Config:
        # allows converting a SQLAlchemy model object directly to this schema
        from_attributes = True
