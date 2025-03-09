import boto3
from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from .models import User
from .schemas import UserCreate, UserUpdate, CognitoTokenResponse

# AWS Cognito configuration
COGNITO_USER_POOL_ID = "your-user-pool-id"  # Replace with your pool ID
COGNITO_APP_CLIENT_ID = "your-client-id"  # Replace with your client ID
COGNITO_REGION = "your-aws-region"  # e.g., "us-east-1"

# Initialize Cognito client
cognito_client = boto3.client('cognito-idp', region_name=COGNITO_REGION)


async def sign_up_user(user_data: UserCreate):
    """Register a new user with Cognito"""
    try:
        response = cognito_client.sign_up(
            ClientId=COGNITO_APP_CLIENT_ID,
            Username=user_data.username,
            Password=user_data.password,
            UserAttributes=[
                {
                    'Name': 'email',
                    'Value': user_data.email
                },
                {
                    'Name': 'name',
                    'Value': user_data.name or user_data.username
                }
            ]
        )
        return response
    except cognito_client.exceptions.UsernameExistsException:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Username already exists"
        )
    except cognito_client.exceptions.InvalidPasswordException:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Password does not meet requirements"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error during signup: {str(e)}"
        )


async def confirm_sign_up(username: str, confirmation_code: str):
    """Confirm user registration with the code they received"""
    try:
        response = cognito_client.confirm_sign_up(
            ClientId=COGNITO_APP_CLIENT_ID,
            Username=username,
            ConfirmationCode=confirmation_code
        )
        return response
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Error confirming registration: {str(e)}"
        )


async def authenticate_user(username: str, password: str) -> CognitoTokenResponse:
    """Authenticate user and return tokens"""
    try:
        response = cognito_client.initiate_auth(
            ClientId=COGNITO_APP_CLIENT_ID,
            AuthFlow="USER_PASSWORD_AUTH",
            AuthParameters={
                "USERNAME": username,
                "PASSWORD": password
            }
        )

        auth_result = response.get("AuthenticationResult")
        if not auth_result:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authentication failed"
            )

        return CognitoTokenResponse(
            access_token=auth_result.get("AccessToken"),
            id_token=auth_result.get("IdToken"),
            refresh_token=auth_result.get("RefreshToken"),
            token_type=auth_result.get("TokenType"),
            expires_in=auth_result.get("ExpiresIn")
        )
    except cognito_client.exceptions.NotAuthorizedException:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Authentication error: {str(e)}"
        )


async def refresh_tokens(refresh_token: str) -> CognitoTokenResponse:
    """Refresh user tokens using a refresh token"""
    try:
        response = cognito_client.initiate_auth(
            ClientId=COGNITO_APP_CLIENT_ID,
            AuthFlow="REFRESH_TOKEN_AUTH",
            AuthParameters={
                "REFRESH_TOKEN": refresh_token
            }
        )

        auth_result = response.get("AuthenticationResult")
        return CognitoTokenResponse(
            access_token=auth_result.get("AccessToken"),
            id_token=auth_result.get("IdToken"),
            refresh_token=refresh_token,  # Cognito doesn't return a new refresh token
            token_type=auth_result.get("TokenType"),
            expires_in=auth_result.get("ExpiresIn")
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Error refreshing token: {str(e)}"
        )


async def get_user_from_cognito_id(db: Session, cognito_id: str):
    """Get user from database by Cognito ID"""
    return db.query(User).filter(User.cognito_id == cognito_id).first()


async def create_user_in_db(db: Session, user_data: UserCreate, cognito_id: str):
    """Create a new user record in the database after successful Cognito registration"""
    db_user = User(
        email=user_data.email.lower().strip(),
        username=user_data.username.lower().strip(),
        name=user_data.name,
        cognito_id=cognito_id
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user


async def get_user_from_user_id(db: Session, user_id: int):
    """Get user from database by user ID"""
    return db.query(User).filter(User.id == user_id).first()


async def update_user(db: Session, db_user: User, user_update: UserUpdate):
    """Update user information in database"""
    if user_update.name is not None:
        db_user.name = user_update.name
    if user_update.bio is not None:
        db_user.bio = user_update.bio
    if user_update.dob is not None:
        db_user.dob = user_update.dob
    if user_update.gender is not None:
        db_user.gender = user_update.gender
    if user_update.location is not None:
        db_user.location = user_update.location
    if user_update.profile_pic is not None:
        db_user.profile_pic = user_update.profile_pic

    db.commit()
    db.refresh(db_user)
    return db_user