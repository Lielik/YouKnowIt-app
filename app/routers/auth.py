# Handles user registration, login, and logout

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_user
from app.core.security import create_access_token, hash_password, verify_password
from app.database import get_db
from app.models.user import User
from app.schemas.auth import UserLogin, UserRegister, UserResponse

router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def register(user_data: UserRegister, db: Session = Depends(get_db)):
    # Check if email is already taken
    if db.query(User).filter(User.email == user_data.email).first():
        raise HTTPException(status_code=400, detail="Email already registered")

    # Check if username is already taken
    if db.query(User).filter(User.username == user_data.username).first():
        raise HTTPException(status_code=400, detail="Username already taken")

    # Create the new user — hash the password before storing
    user = User(
        username=user_data.username,
        email=user_data.email,
        password_hash=hash_password(user_data.password),
    )
    db.add(user)
    db.commit()
    db.refresh(user)  # reload from DB to get the generated id and created_at
    return user


@router.post("/login")
def login(user_data: UserLogin, response: Response, db: Session = Depends(get_db)):
    # Find user by email
    user = db.query(User).filter(User.email == user_data.email).first()

    # Use the same error for wrong email and wrong password
    # — never tell the user which one was wrong (security best practice)
    if not user or not verify_password(user_data.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    # Create JWT token with the user's id as the subject
    token = create_access_token(data={"sub": str(user.id)})

    # Set token as an HTTP-only cookie — JS cannot read it, prevents XSS attacks
    response.set_cookie(
        key="access_token",
        value=token,
        httponly=True,   # not accessible via JavaScript
        samesite="lax",  # protects against CSRF attacks
        secure=False,    # set to True in production (requires HTTPS)
    )
    return {"message": "Login successful"}


@router.post("/logout")
def logout(response: Response):
    # Delete the cookie by setting it to expire immediately
    response.delete_cookie("access_token")
    return {"message": "Logged out successfully"}


@router.get("/me", response_model=UserResponse)
def me(current_user: User = Depends(get_current_user)):
    # Returns the currently logged in user's info
    return current_user
