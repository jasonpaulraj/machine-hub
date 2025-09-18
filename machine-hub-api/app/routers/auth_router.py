from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer
from sqlalchemy.orm import Session
from datetime import timedelta
from typing import List

from ..database import get_db
from .. import crud, schemas, auth

router = APIRouter()
security = HTTPBearer()


@router.post("/login", response_model=schemas.Token)
async def login(user_credentials: schemas.UserLogin, db: Session = Depends(get_db)):
    """Authenticate user and return JWT token"""
    user = auth.authenticate_user(
        db, user_credentials.username, user_credentials.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token_expires = timedelta(minutes=auth.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = auth.create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )

    return {
        "access_token": access_token,
        "token_type": "bearer"
    }


@router.post("/register", response_model=schemas.User)
async def register(user: schemas.UserCreate, db: Session = Depends(get_db)):
    """Register a new user"""
    # Check if user already exists
    db_user = crud.get_user_by_username(db, username=user.username)
    if db_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already registered"
        )

    # Create new user
    return crud.create_user(db=db, user=user)


@router.get("/me", response_model=schemas.User)
async def read_users_me(current_user=Depends(auth.get_current_active_user)):
    """Get current user information"""
    return current_user


@router.get("/users", response_model=List[schemas.User])
async def read_users(
    skip: int = 0,
    limit: int = 100,
    current_user=Depends(auth.get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get list of users (requires authentication)"""
    users = crud.get_users(db, skip=skip, limit=limit)
    return users


@router.post("/verify-token")
async def verify_token(current_user=Depends(auth.get_current_active_user)):
    """Verify if the current token is valid"""
    return {
        "valid": True,
        "user": {
            "id": current_user.id,
            "username": current_user.username,
            "is_active": current_user.is_active
        }
    }
