from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from typing import List, Optional
from pi3.models.users import User
from pi3.auth.dependencies import get_current_active_user
from pi3.auth.utils import get_password_hash

router = APIRouter(prefix="/users", tags=["users"])

class UserCreate(BaseModel):
    name: str
    username: str
    password: str

class UserUpdate(BaseModel):
    name: Optional[str] = None
    username: Optional[str] = None

class UserResponse(UserCreate):
    id: int
    
    class Config:
        from_attributes = True

@router.post("/", response_model=UserResponse)
async def create_user(user: UserCreate, current_user: User = Depends(get_current_active_user)):
    """Create a new user (admin only)"""
    # Check if user already exists
    existing_user = await User.filter(username=user.username).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already registered"
        )
    
    # Create new user with hashed password
    hashed_password = get_password_hash(user.password)
    db_user = await User.create(
        name=user.name,
        username=user.username,
        hashed_password=hashed_password
    )
    
    return UserResponse(
        id=db_user.id,
        name=db_user.name,
        username=db_user.username,
        password=""  # Don't return the password
    )

@router.get("/", response_model=List[UserResponse])
async def get_users(current_user: User = Depends(get_current_active_user)):
    """Get all users (admin only)"""
    users = await User.all()
    return [UserResponse(
        id=user.id,
        name=user.name,
        username=user.username,
        password=""
    ) for user in users]

@router.get("/{user_id}", response_model=UserResponse)
async def get_user(user_id: int, current_user: User = Depends(get_current_active_user)):
    """Get a specific user by ID (admin only)"""
    user = await User.filter(id=user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    return UserResponse(
        id=user.id,
        name=user.name,
        username=user.username,
        password=""
    )

@router.put("/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: int, 
    user_update: UserUpdate, 
    current_user: User = Depends(get_current_active_user)
):
    """Update a specific user by ID (admin only)"""
    db_user = await User.filter(id=user_id).first()
    if not db_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Update fields if provided
    if user_update.name is not None:
        db_user.name = user_update.name
    if user_update.username is not None:
        # Check if new username already exists (excluding this user)
        existing_user = await User.filter(username=user_update.username).first()
        if existing_user and existing_user.id != user_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Username already taken"
            )
        db_user.username = user_update.username
    
    await db_user.save()
    
    return UserResponse(
        id=db_user.id,
        name=db_user.name,
        username=db_user.username,
        password=""
    )

@router.delete("/{user_id}")
async def delete_user(user_id: int, current_user: User = Depends(get_current_active_user)):
    """Delete a specific user by ID (admin only)"""
    db_user = await User.filter(id=user_id).first()
    if not db_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    await db_user.delete()
    return {"message": "User deleted successfully"}
