from app import db, app
from app import LessonSlot

with app.app_context():
    # Fetch all lesson slots
    lesson_slots = LessonSlot.query.order_by(LessonSlot.start_time).all()

    # Initialize previous slot to None
    prev_slot = None

    for slot in lesson_slots:
        # If the current slot is identical to the previous one, delete it
        if prev_slot and slot.start_time == prev_slot.start_time and slot.end_time == prev_slot.end_time and slot.teacher_id == prev_slot.teacher_id:
            db.session.delete(slot)
        else:
            prev_slot = slot

    db.session.commit()
    print("Deleted duplicate lesson slots.")