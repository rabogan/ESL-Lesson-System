"""
This script removes expired lesson slots from the database.

Expired slots are defined as those that ended more than a day ago and have not been booked.
"""

from datetime import datetime, timedelta, timezone
from app import db, LessonSlot

def remove_expired_slots():
    """
    Remove expired lesson slots from the database.

    An expired slot is one where the end time is more than a day ago and the slot is not booked.
    """
    # Calculate the current time minus one day
    now = datetime.now(timezone.utc) - timedelta(days=1)

    # Query for expired slots that are not booked
    expired_slots = LessonSlot.query.filter(
        LessonSlot.end_time < now,
        LessonSlot.is_booked == False
    ).all()

    # Delete the expired slots
    for slot in expired_slots:
        db.session.delete(slot)

    # Commit the changes to the database
    db.session.commit()

if __name__ == "__main__":
    remove_expired_slots()
