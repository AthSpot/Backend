from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from datetime import datetime

from .models import Team, Booking, Activity, ActivityPhoto
from .schemas import TeamCreate, TeamUpdate, BookingCreate, BookingUpdate, ActivityCreate, ActivityUpdate
from ..auth.service import get_user_from_user_id


# Team services
async def create_team(db: Session, team_data: TeamCreate, leader_id: int):
    # Check if the leader exists
    leader = await get_user_from_user_id(db, leader_id)
    if not leader:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Leader not found")

    # Create the team
    db_team = Team(
        name=team_data.name,
        description=team_data.description,
        max_members=team_data.max_members,
        leader_id=leader_id
    )

    db.add(db_team)
    db.commit()
    db.refresh(db_team)

    # Add the leader as a member
    await add_member_to_team(db, db_team.id, leader_id)

    # Update user's team count
    leader.teams_count += 1
    db.commit()

    return db_team


async def get_team(db: Session, team_id: int):
    return db.query(Team).filter(Team.id == team_id).first()


async def update_team(db: Session, team_id: int, team_data: TeamUpdate, user_id: int):
    db_team = await get_team(db, team_id)
    if not db_team:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Team not found")

    # Check if the user is the team leader
    if db_team.leader_id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only the team leader can update the team"
        )

    # Update fields
    db_team.name = team_data.name or db_team.name
    db_team.description = team_data.description or db_team.description
    db_team.max_members = team_data.max_members or db_team.max_members
    db_team.status = team_data.status or db_team.status
    db_team.team_photo = team_data.team_photo or db_team.team_photo

    db.commit()
    db.refresh(db_team)
    return db_team


async def delete_team(db: Session, team_id: int, user_id: int):
    db_team = await get_team(db, team_id)
    if not db_team:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Team not found")

    # Check if the user is the team leader
    if db_team.leader_id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only the team leader can delete the team"
        )

    # Set team status to archived instead of deleting
    db_team.status = "archived"
    db.commit()
    return {"message": "Team archived successfully"}


async def add_member_to_team(db: Session, team_id: int, user_id: int):
    db_team = await get_team(db, team_id)
    if not db_team:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Team not found")

    # Check if the user exists
    user = await get_user_from_user_id(db, user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    # Check if the user is already a member
    if user in db_team.members:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User is already a member of this team"
        )

    # Check team size
    if len(db_team.members) >= db_team.max_members:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Team is already at maximum capacity"
        )

    # Add user to team
    db_team.members.append(user)

    # Update user's team count
    user.teams_count += 1

    db.commit()
    return {"message": "User added to team successfully"}


async def remove_member_from_team(db: Session, team_id: int, user_id: int, leader_id: int):
    db_team = await get_team(db, team_id)
    if not db_team:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Team not found")

    # Check if the requester is the team leader
    if db_team.leader_id != leader_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only the team leader can remove members"
        )

    # Check if user is the leader (cannot remove self)
    if user_id == leader_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Team leader cannot be removed from the team"
        )

    # Get the user to remove
    user = await get_user_from_user_id(db, user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    # Check if the user is a member
    if user not in db_team.members:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User is not a member of this team"
        )

    # Remove user from team
    db_team.members.remove(user)

    # Update user's team count
    user.teams_count -= 1

    db.commit()
    return {"message": "User removed from team successfully"}


# Booking services
async def create_booking(db: Session, booking_data: BookingCreate, user_id: int):
    # Check if the team exists
    db_team = await get_team(db, booking_data.team_id)
    if not db_team:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Team not found")

    # Check if the user is the team leader
    if db_team.leader_id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only the team leader can create bookings"
        )

    # Check if the venue exists
    from ..venues.service import get_venue
    db_venue = await get_venue(db, booking_data.venue_id)
    if not db_venue:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Venue not found")

    # Calculate the total cost
    duration_hours = (booking_data.end_time - booking_data.start_time).total_seconds() / 3600
    total_cost = duration_hours * db_venue.price_per_hour if db_venue.price_per_hour else 0

    # Create booking
    db_booking = Booking(
        venue_id=booking_data.venue_id,
        team_id=booking_data.team_id,
        start_time=booking_data.start_time,
        end_time=booking_data.end_time,
        total_cost=total_cost
    )

    db.add(db_booking)
    db.commit()
    db.refresh(db_booking)

    return db_booking


async def get_booking(db: Session, booking_id: int):
    return db.query(Booking).filter(Booking.id == booking_id).first()


async def update_booking(db: Session, booking_id: int, booking_data: BookingUpdate, user_id: int):
    db_booking = await get_booking(db, booking_id)
    if not db_booking:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Booking not found")

    # Check if the user is the team leader
    if db_booking.team.leader_id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only the team leader can update bookings"
        )

    # Update fields
    if booking_data.status:
        db_booking.status = booking_data.status
    if booking_data.total_cost is not None:
        db_booking.total_cost = booking_data.total_cost
    if booking_data.is_paid is not None:
        db_booking.is_paid = booking_data.is_paid

    db.commit()
    db.refresh(db_booking)
    return db_booking


async def cancel_booking(db: Session, booking_id: int, user_id: int):
    db_booking = await get_booking(db, booking_id)
    if not db_booking:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Booking not found")

    # Check if the user is the team leader
    if db_booking.team.leader_id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only the team leader can cancel bookings"
        )

    # Set booking status to cancelled
    db_booking.status = "cancelled"
    db.commit()

    return {"message": "Booking cancelled successfully"}


# Activity services
async def create_activity(db: Session, activity_data: ActivityCreate, user_id: int):
    # Check if the team exists
    db_team = await get_team(db, activity_data.team_id)
    if not db_team:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Team not found")

    # Check if the user is the team leader
    if db_team.leader_id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only the team leader can create activities"
        )

    # Check if venue exists if provided
    if activity_data.venue_id:
        from ..venues.service import get_venue
        db_venue = await get_venue(db, activity_data.venue_id)
        if not db_venue:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Venue not found")

    # Create activity
    db_activity = Activity(
        team_id=activity_data.team_id,
        venue_id=activity_data.venue_id,
        activity_type=activity_