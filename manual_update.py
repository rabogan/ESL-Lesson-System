# Example script to update the existing booking
from app import db, app
from app import LessonSlot

with app.app_context():
    # Delete all LessonSlot records
    db.session.query(LessonSlot).delete()
    db.session.commit()

print("Removed all LessonSlot records successfully!")