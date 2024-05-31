from app import app, db
from app import LessonRecord, LessonSlot, Teacher, Student
from datetime import datetime, timedelta

with app.app_context():
    # Step 1: Delete all existing LessonRecord entries
    LessonRecord.query.delete()
    db.session.commit()

    # Step 2: Fetch existing students and teacher (or create them if necessary)
    teacher = Teacher.query.get(1)  # Assuming a teacher with ID 1 exists
    student = Student.query.get(1)  # Assuming a student with ID 1 exists

    # Step 3: Create new lesson slots and lesson records
    for i in range(1, 6):
        start_time = datetime.utcnow() + timedelta(days=i)
        end_time = start_time + timedelta(hours=1)
        
        lesson_slot = LessonSlot(
            teacher_id=teacher.id,
            start_time=start_time,
            end_time=end_time,
            is_booked=True
        )
        db.session.add(lesson_slot)
        db.session.commit()
        
        lesson_record = LessonRecord(
            student_id=student.id,
            teacher_id=teacher.id,
            lesson_slot_id=lesson_slot.id,
            strengths="Good vocabulary",
            areas_to_improve="Grammar",
            new_words=["bureaucracy", "food truck", "grief"],
            new_phrases=["I suck at English", "My family is ashamed of my idiocy", "Think positive!"],
            lesson_summary="Lesson summary",
            date=datetime.utcnow()
        )
        db.session.add(lesson_record)

    db.session.commit()

    print("Lesson records reset successfully.")
