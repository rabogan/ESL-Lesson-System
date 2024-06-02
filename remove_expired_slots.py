from datetime import datetime, timedelta, timezone
from app import db, LessonSlot

def remove_expired_slots():
    now = datetime.now(timezone.utc) - timedelta(days=1)
    expired_slots = LessonSlot.query.filter(
        LessonSlot.end_time < now,
        LessonSlot.is_booked == False
    ).all()

    for slot in expired_slots:
        db.session.delete(slot)

    db.session.commit()

if __name__ == "__main__":
    remove_expired_slots()