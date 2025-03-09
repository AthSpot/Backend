from fastapi import APIRouter, Depends, UploadFile, File, Request, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from ..s3_database import get_db
from ..utils.s3_service import upload_file_to_s3, delete_file_from_s3

router = APIRouter(prefix="/uploads", tags=["uploads"])


@router.post("/profile-picture", status_code=status.HTTP_201_CREATED)
async def upload_profile_picture(
        file: UploadFile = File(...),
        request: Request = None,
        db: Session = Depends(get_db)
):
    """Upload a user profile picture"""
    # Check if user is authenticated
    user_id = request.state.user_id
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated"
        )

    # Validate file type
    allowed_types = ["image/jpeg", "image/png", "image/gif"]
    if file.content_type not in allowed_types:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only JPEG, PNG, and GIF images are allowed"
        )

    # Upload file to S3
    upload_result = await upload_file_to_s3(
        file_content=file.file,
        file_name=file.filename,
        content_type=file.content_type,
        file_prefix="profile-pictures",
        metadata={"user_id": str(user_id)}
    )

    # Update user profile in the database
    from ..auth.service import get_user_from_cognito_id, update_user
    from ..auth.schemas import UserUpdate

    user = await get_user_from_cognito_id(db, user_id)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    # Delete previous profile picture if exists
    if user.profile_pic:
        await delete_file_from_s3(user.profile_pic)

    # Update user with new profile picture URL
    user_update = UserUpdate(profile_pic=upload_result["url"])
    updated_user = await update_user(db, user, user_update)

    return {
        "message": "Profile picture uploaded successfully",
        "url": upload_result["url"]
    }


@router.post("/team-photo/{team_id}", status_code=status.HTTP_201_CREATED)
async def upload_team_photo(
        team_id: int,
        file: UploadFile = File(...),
        request: Request = None,
        db: Session = Depends(get_db)
):
    """Upload a team photo"""
    # Check if user is authenticated
    user_id = request.state.user_id
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated"
        )

    # Validate file type
    allowed_types = ["image/jpeg", "image/png", "image/gif"]
    if file.content_type not in allowed_types:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only JPEG, PNG, and GIF images are allowed"
        )

    # Get the team
    from ..activity.service import get_team
    team = await get_team(db, team_id)

    if not team:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Team not found"
        )

    # Check if user is the team leader
    from ..auth.service import get_user_from_cognito_id
    user = await get_user_from_cognito_id(db, user_id)

    if not user or team.leader_id != user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only the team leader can update the team photo"
        )

    # Upload file to S3
    upload_result = await upload_file_to_s3(
        file_content=file.file,
        file_name=file.filename,
        content_type=file.content_type,
        file_prefix=f"team-photos/{team_id}",
        metadata={"team_id": str(team_id)}
    )

    # Update team photo in the database
    from ..activity.service import update_team
    from ..activity.schemas import TeamUpdate

    # Delete previous team photo if exists
    if team.team_photo:
        await delete_file_from_s3(team.team_photo)

    # Update team with new photo URL
    team_update = TeamUpdate(team_photo=upload_result["url"])
    updated_team = await update_team(db, team_id, team_update, user.id)

    return {
        "message": "Team photo uploaded successfully",
        "url": upload_result["url"]
    }


@router.post("/activity-photos/{activity_id}", status_code=status.HTTP_201_CREATED)
async def upload_activity_photos(
        activity_id: int,
        files: List[UploadFile] = File(...),
        caption: str = None,
        request: Request = None,
        db: Session = Depends(get_db)
):
    """Upload photos for an activity"""
    # Check if user is authenticated
    user_id = request.state.user_id
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated"
        )

    # Get the activity
    from ..activity.models import Activity
    activity = db.query(Activity).filter(Activity.id == activity_id).first()

    if not activity:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Activity not found"
        )

    # Get the user
    from ..auth.service import get_user_from_cognito_id
    user = await get_user_from_cognito_id(db, user_id)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    # Check if user is part of the team
    team_member_ids = [member.id for member in activity.team.members]
    if user.id not in team_member_ids and user.id != activity.team.leader_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You must be a member of the team to upload photos"
        )

    uploaded_photos = []

    # Upload each file to S3
    for file in files:
        # Validate file type
        allowed_types = ["image/jpeg", "image/png", "image/gif"]
        if file.content_type not in allowed_types:
            continue  # Skip invalid files

        # Upload file to S3
        upload_result = await upload_file_to_s3(
            file_content=file.file,
            file_name=file.filename,
            content_type=file.content_type,
            file_prefix=f"activity-photos/{activity_id}",
            metadata={
                "activity_id": str(activity_id),
                "user_id": str(user.id)
            }
        )

        # Create activity photo record
        from ..activity.models import ActivityPhoto

        photo = ActivityPhoto(
            activity_id=activity_id,
            user_id=user.id,
            photo_url=upload_result["url"],
            caption=caption
        )

        db.add(photo)
        uploaded_photos.append(upload_result["url"])

    if not uploaded_photos:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No valid photos were uploaded"
        )

    db.commit()

    return {
        "message": f"{len(uploaded_photos)} photos uploaded successfully",
        "urls": uploaded_photos
    }


@router.post("/venue-photos/{venue_id}", status_code=status.HTTP_201_CREATED)
async def upload_venue_photos(
        venue_id: int,
        files: List[UploadFile] = File(...),
        caption: str = None,
        is_primary: bool = False,
        request: Request = None,
        db: Session = Depends(get_db)
):
    """Upload photos for a venue"""
    # Check if user is authenticated
    user_id = request.state.user_id
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated"
        )

    # Get the venue
    from ..venues.models import Venue
    venue = db.query(Venue).filter(Venue.id == venue_id).first()

    if not venue:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Venue not found"
        )

    # Get the user
    from ..auth.service import get_user_from_cognito_id
    user = await get_user_from_cognito_id(db, user_id)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    # Check if user is the venue owner
    if user.id != venue.owner_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only the venue owner can upload photos"
        )

    uploaded_photos = []

    # Upload each file to S3
    for file in files:
        # Validate file type
        allowed_types = ["image/jpeg", "image/png", "image/gif"]
        if file.content_type not in allowed_types:
            continue  # Skip invalid files

        # Upload file to S3
        upload_result = await upload_file_to_s3(
            file_content=file.file,
            file_name=file.filename,
            content_type=file.content_type,
            file_prefix=f"venue-photos/{venue_id}",
            metadata={"venue_id": str(venue_id)}
        )

        # Create venue photo record
        from ..venues.models import VenuePhoto

        # If this is a primary photo and is_primary is True, set all other photos to not primary
        if is_primary:
            db.query(VenuePhoto