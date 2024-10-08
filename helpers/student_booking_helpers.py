from models import LessonSlot, Booking, LessonRecord
from database import db
from datetime import datetime, timezone
from helpers.time_helpers import ensure_timezone_aware
from sqlalchemy.orm import joinedload


def fetch_available_slots(_, start_of_week_utc, end_of_week_utc, teacher_id=None):
    """
    Fetch available lesson slots for a student.

    Args:
        _ (Student): The student object.
        start_of_week_utc (datetime): The start of the week in UTC.
        end_of_week_utc (datetime): The end of the week in UTC.
        teacher_id (int, optional): The ID of the teacher to filter by. Defaults to None.

    Returns:
        list: A list of available LessonSlot objects.
    """
    available_slots = LessonSlot.query.filter(
        LessonSlot.start_time.between(start_of_week_utc, end_of_week_utc),
        LessonSlot.start_time > datetime.now(timezone.utc),
        LessonSlot.is_booked == False,
        (LessonSlot.teacher_id == teacher_id) if teacher_id is not None else True,
    ).order_by(LessonSlot.start_time.asc()).all()
    return available_slots


def convert_slots_to_dict(lesson_slots):
    """
    Convert lesson slot objects to a dictionary format.

    Args:
        lesson_slots (list): A list of LessonSlot objects.

    Returns:
        list: A list of dictionaries representing the lesson slots.
    """
    available_slots_dict = [
        {
            'id': slot.id,
            'start_time': slot.start_time.isoformat(),
            'end_time': slot.end_time.isoformat(),
            'teacher_id': slot.teacher.id,
            'teacher_username': slot.teacher.username,
        }
        for slot in lesson_slots
    ]
    return available_slots_dict


def update_student_booking(session, form, student, current_time):
    """
    Update a student's booking for a lesson.

    Args:
        session (dict): The session object.
        form (Form): The form containing booking data.
        student (Student): The student object.
        current_time (datetime): The current time.

    Returns:
        tuple: The lesson record and an error message if any.
    """
    lesson_slot_id = form.lesson_slot.data
    teacher_id = form.teacher.data

    lesson_slot = db.session.get(LessonSlot, lesson_slot_id)
    if lesson_slot is None or lesson_slot.is_booked or ensure_timezone_aware(lesson_slot.start_time, student.timezone) < current_time:
        return None, 'Invalid or unavailable lesson slot selected.'

    if student.lessons_purchased <= student.number_of_lessons:
        return None, 'Not enough points to book a lesson.'

    lesson_record = LessonRecord(student_id=student.id, teacher_id=teacher_id, lesson_slot_id=lesson_slot.id)
    db.session.add(lesson_record)
    db.session.flush()

    booking = Booking(student_id=student.id, lesson_slot_id=lesson_slot.id, status='booked', lesson_record_id=lesson_record.id)
    db.session.add(booking)

    lesson_slot.is_booked = True
    student.number_of_lessons += 1

    session['available_slots'] = [slot for slot in session['available_slots'] if slot['id'] != lesson_slot_id]

    try:
        db.session.commit()
        return lesson_record, None
    except Exception as e:
        db.session.rollback()
        return None, f'Error booking lesson: {e}'
    

def fetch_and_format_slots(student, teacher_id, start_of_week, end_of_week, user_timezone):
    """
    Fetch and format lesson slots for a student and teacher.

    Args:
        student (Student): The student object.
        teacher_id (int): The ID of the teacher.
        start_of_week (datetime): The start of the week.
        end_of_week (datetime): The end of the week.
        user_timezone (timezone): The user's timezone.

    Returns:
        list: A list of dictionaries representing the lesson slots.
    """
    current_time_utc = datetime.now(timezone.utc)

    # Get the student's existing bookings
    existing_bookings = Booking.query.options(joinedload(Booking.lesson_slot)).filter(
        Booking.student_id == student.id,
        LessonSlot.start_time >= start_of_week,
        LessonSlot.end_time <= end_of_week
    ).all()

    # Get the start times of the LessonSlots associated with the existing bookings
    existing_booking_start_times = [booking.lesson_slot.start_time for booking in existing_bookings]

    slots = LessonSlot.query.filter(
        LessonSlot.teacher_id == teacher_id,
        LessonSlot.is_booked == False,
        LessonSlot.start_time >= start_of_week,
        LessonSlot.start_time <= end_of_week,
        LessonSlot.start_time >= current_time_utc
    ).all()

    # Filter out slots that start at the same time as existing bookings
    slots = [slot for slot in slots if slot.start_time not in existing_booking_start_times]

    slots_dict = [{
        'id': slot.id,
        'start_time': slot.start_time.replace(tzinfo=timezone.utc).astimezone(user_timezone).strftime('%Y-%m-%d %I:%M %p'),
        'end_time': slot.end_time.replace(tzinfo=timezone.utc).astimezone(user_timezone).strftime('%I:%M %p'),
        'teacher': slot.teacher.username
    } for slot in slots]

    return slots_dict
