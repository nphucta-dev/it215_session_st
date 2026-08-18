from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status

from dependencies.authentication import get_current_user
from models.models import User
from schemas.schemas import LoginRequest, Token, UserRead
from services.auth_service import authenticate_user, create_access_token
from core.database import get_db
from sqlalchemy.orm import Session

router = APIRouter(prefix="/api/v1/auth", tags=["Authentication"])


@router.post("/login", response_model=Token)
def login(payload: LoginRequest, db: Annotated[Session, Depends(get_db)]):
    user = authenticate_user(db, payload.email, payload.password)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="User account is inactive")
    return Token(access_token=create_access_token(user))


@router.get("/me", response_model=UserRead)
def me(current_user: Annotated[User, Depends(get_current_user)]):
    return current_user
