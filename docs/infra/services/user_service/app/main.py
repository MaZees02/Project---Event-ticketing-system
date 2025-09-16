import os
from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlmodel import SQLModel, Session, select
from datetime import timedelta
from dotenv import load_dotenv

load_dotenv()

from .db import engine, get_session
from .models import User
from .schemas import UserCreate, UserRead, UserUpdate, Token
from .auth import get_password_hash, authenticate_user, create_access_token, get_current_user

app = FastAPI(title="user_service")

@app.on_event("startup")
def on_startup():
    SQLModel.metadata.create_all(engine)

@app.get("/health", tags=["health"])
def health():
    return {"status": "ok"}

@app.post("/auth/register", response_model=UserRead, tags=["auth"])
def register(user_in: UserCreate, session: Session = Depends(get_session)):
    # check existing
    statement = select(User).where(User.email == user_in.email)
    existing = session.exec(statement).first()
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")
    user = User(
        email=user_in.email,
        hashed_password=get_password_hash(user_in.password),
        full_name=user_in.full_name
    )
    session.add(user)
    session.commit()
    session.refresh(user)
    return user

@app.post("/auth/token", response_model=Token, tags=["auth"])
def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends(), session: Session = Depends(get_session)):
    user = authenticate_user(session, form_data.username, form_data.password)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Incorrect email or password", headers={"WWW-Authenticate": "Bearer"})
    access_token_expires = timedelta(minutes=int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "60")))
    access_token = create_access_token(data={"sub": user.email}, expires_delta=access_token_expires)
    return {"access_token": access_token, "token_type": "bearer"}

# Get current user
@app.get("/users/me", response_model=UserRead, tags=["users"])
def read_users_me(db: Session = Depends(get_session), current_user_call = Depends(get_current_user)):
    # current_user_call is a function expecting db
    user = current_user_call(db)
    return user

# Update profile (partial)
@app.put("/users/me", response_model=UserRead, tags=["users"])
def update_user(user_update: UserUpdate, db: Session = Depends(get_session), current_user_call = Depends(get_current_user)):
    user = current_user_call(db)
    if user_update.full_name is not None:
        user.full_name = user_update.full_name
    if user_update.is_active is not None:
        user.is_active = user_update.is_active
    db.add(user)
    db.commit()
    db.refresh(user)
    return user

# Admin-only: List users (for demo; in prod protect admin routes)
@app.get("/users", response_model=list[UserRead], tags=["users"])
def list_users(db: Session = Depends(get_session)):
    statement = select(User)
    results = db.exec(statement).all()
    return results
