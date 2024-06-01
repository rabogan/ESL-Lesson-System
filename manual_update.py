
# Example script to update the existing booking
from app import db, app
from app import Booking, LessonRecord

with app.app_context():
    # Fetch all bookings
    bookings = Booking.query.all()
    
    for booking in bookings:
        # Find the corresponding lesson record
        lesson_record = LessonRecord.query.filter_by(student_id=booking.student_id, lesson_slot_id=booking.lesson_slot_id).first()
        
        if lesson_record:
            booking.lesson_record_id = lesson_record.id

    db.session.commit()
    print("Updated lesson_record_id in bookings.")