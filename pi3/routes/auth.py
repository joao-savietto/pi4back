from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel

from pi3.auth.dependencies import get_current_user
from pi3.auth.utils import (
    create_access_token,
    create_refresh_token,
    verify_password,
    verify_token,
)
from pi3.models.users import User

router = APIRouter(prefix="/auth", tags=["authentication"])


class UserCreate(BaseModel):
    name: str
    username: str
    password: str


class UserLogin(BaseModel):
    username: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str
    refresh_token: Optional[str] = None


class RefreshTokenRequest(BaseModel):
    refresh_token: str


class TokenRefreshResponse(BaseModel):
    access_token: str
    token_type: str


class UserInfo(BaseModel):
    id: int
    name: str
    username: str


@router.post("/login", response_model=TokenResponse)
async def login_user(credentials: UserLogin):
    """Login user and return access token"""
    # Find user by username
    user = await User.filter(username=credentials.username).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Verify password
    if not verify_password(credentials.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Create tokens
    access_token = create_access_token(data={"sub": user.username})
    refresh_token = create_refresh_token(data={"sub": user.username})

    return TokenResponse(
        access_token=access_token,
        token_type="bearer",
        refresh_token=refresh_token,
    )


@router.get("/me", response_model=UserInfo)
async def get_current_user_info(
    current_user: User = Depends(get_current_user),
):
    """Get current authenticated user info"""
    return UserInfo(
        id=current_user.id,
        name=current_user.name,
        username=current_user.username,
    )


@router.post("/refresh", response_model=TokenRefreshResponse)
async def refresh_access_token(request: RefreshTokenRequest):
    """Obtain a new access token using a refresh token"""
    # Verify the refresh token
    username = verify_token(request.refresh_token)
    if username is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Create a new access token for the user
    new_access_token = create_access_token(data={"sub": username})

    return TokenRefreshResponse(
        access_token=new_access_token,
        token_type="bearer",
    )
