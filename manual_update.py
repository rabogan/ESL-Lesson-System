
# Example script to update the existing booking
from app import db, app
from app import Booking, LessonRecord

# Fetch the existing booking and lesson record
with app.app_context():
    # Fetch the existing booking and lesson record
    booking = Booking.query.first()
    lesson_record = LessonRecord.query.first()

    # Ensure both booking and lesson_record exist
    if booking and lesson_record:
        # Link them
        booking.lesson_record_id = lesson_record.id

        # Commit the changes
        db.session.commit()
        print("Booking updated with lesson_record_id.")
    else:
        print("Booking or LessonRecord not found.")
