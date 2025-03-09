from fastapi import APIRouter, Depends, status, HTTPException, Request
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from typing import Optional

from .schemas import UserCreate, UserUpdate, User as UserSchema, CognitoTokenResponse
from ..s3_database import get_db
from .service import (
    sign_up_user,
    confirm_sign_up,
    authenticate_user,
    refresh_tokens,
    create_user_in_db,
    get_user_from_cognito_id,
    get_user_from_user_id,
    update_user,
)

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/signup", status_code=status.HTTP_201_CREATED)
async def signup(user: UserCreate, db: Session = Depends(get_db)):
    """Register a new user"""
    # Register with Cognito
    response = await sign_up_user(user)

    # Return user data and message to confirm email
    return {
        "message": "User created successfully. Please check your email for confirmation code.",
        "username": user.username,
        "user_sub": response["UserSub"]  # This is the Cognito user ID
    }


@router.post("/confirm", status_code=status.HTTP_200_OK)
async def confirm_registration(username: str, confirmation_code: str, db: Session = Depends(get_db)):
    """Confirm user registration with verification code"""
    # Confirm user in Cognito
    await confirm_sign_up(username, confirmation_code)

    # Create user in database (you might want to wait for the first login instead)
    # This would be done when the user first logs in

    return {"message": "User confirmed successfully. You can now log in."}


@router.post("/login", response_model=CognitoTokenResponse, status_code=status.HTTP_200_OK)
async def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    """Authenticate user and return tokens"""
    # Authenticate with Cognito
    token_response = await authenticate_user(form_data.username, form_data.password)

    # At this point, you might want to create the user in the database if it doesn't exist
    # You'd need to extract the cognito_id from the JWT token

    return token_response


@router.post("/refresh", response_model=CognitoTokenResponse)
async def refresh(refresh_token: str):
    """Refresh access token using refresh token"""
    return await refresh_tokens(refresh_token)


@router.get("/profile", response_model=UserSchema)
async def get_profile(request: Request, db: Session = Depends(get_db)):
    """Get current user profile"""
    # The user's Cognito ID should be extracted from the token in middleware
    cognito_id = request.state.user_id

    if not cognito_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated"
        )

    # Get user from database
    user = await get_user_from_cognito_id(db, cognito_id)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    return user


@router.put("/profile", response_model=UserSchema)
async def update_profile(
        user_update: UserUpdate,
        request: Request,
        db: Session = Depends(get_db)
):
    """Update user profile"""
    # The user's Cognito ID should be extracted from the token in middleware
    cognito_id = request.state.user_id

    if not cognito_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated"
        )

    # Get user from database
    user = await get_user_from_cognito_id(db, cognito_id)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    # Update user
    updated_user = await update_user(db, user, user_update)

    return updated_user