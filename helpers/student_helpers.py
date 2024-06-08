from models import Booking, LessonSlot, LessonRecord, Student
from database import db
import logging

def cancel_student_lesson(lesson_id, student_id):
    """
    Cancel a lesson for a student.
    
    Args:
        lesson_id (int): The ID of the lesson slot.
        student_id (int): The ID of the student.

    Returns:
        (bool, str): Success status and message.
    """
    # Fetch the booking from the database
    booking = Booking.query.filter_by(lesson_slot_id=lesson_id, student_id=student_id).first()
    if booking is None:
        return False, 'Invalid booking ID'

    # Fetch the associated lesson slot
    lesson_slot = db.session.get(LessonSlot, lesson_id)
    if lesson_slot is None:
        return False, 'Associated lesson slot not found'

    # Fetch the lesson record from the database
    lesson_record = LessonRecord.query.filter_by(id=booking.lesson_record_id).first()
    if lesson_record is not None:
        # Delete the lesson record entry
        db.session.delete(lesson_record)

    # Delete the booking entry
    db.session.delete(booking)

    # Update the lesson slot to set is_booked to False
    lesson_slot.is_booked = False

    # Update the student's lesson counts
    student = db.session.get(Student, student_id)
    if student is not None:
        student.number_of_lessons -= 1
    else:
        return False, 'Student not found'

    # Commit the changes to the database
    try:
        db.session.commit()
        return True, 'Lesson cancelled successfully'
    except Exception as e:
        db.session.rollback()
        logging.error(f"Error cancelling lesson: {e}")
        return False, f'Error cancelling lesson: {e}'


def get_student_by_id(student_id):
    """
    Fetch a student by their ID.

    Args:
        student_id (int): The ID of the student to fetch.

    Returns:
        Student: The student if found, else None.
    """
    return db.session.get(Student, student_id)


def update_student_profile(form, profile):
    """
    Update the student's profile with data from the form.

    Args:
        form (Form): The form containing updated profile data.
        profile (StudentProfile): The student's profile to update.
    """
    profile.hometown = form.hometown.data.strip() if form.hometown.data else ''
    profile.goal = form.goal.data.strip() if form.goal.data else ''
    profile.hobbies = form.hobbies.data.strip() if form.hobbies.data else ''
    profile.correction_style = form.correction_style.data.strip() if form.correction_style.data else ''
    profile.english_weakness = form.english_weakness.data.strip() if form.english_weakness.data else ''