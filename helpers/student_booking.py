from models import LessonSlot, Booking, LessonRecord
from database import db
from datetime import datetime, timezone
from helpers.time_helpers import ensure_timezone_aware


def fetch_available_slots(student, start_of_week_utc, end_of_week_utc, teacher_id=None):
    available_slots = LessonSlot.query.filter(
        LessonSlot.start_time.between(start_of_week_utc, end_of_week_utc),
        LessonSlot.start_time > datetime.now(timezone.utc),
        LessonSlot.is_booked == False,
        (LessonSlot.teacher_id == teacher_id) if teacher_id is not None else True,
    ).order_by(LessonSlot.start_time.asc()).all()
    return available_slots

def convert_slots_to_dict(lesson_slots):
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
    current_time_utc = datetime.now(timezone.utc)

    slots = LessonSlot.query.filter(
        LessonSlot.teacher_id == teacher_id,
        LessonSlot.is_booked == False,
        LessonSlot.start_time >= start_of_week,
        LessonSlot.start_time <= end_of_week,
        LessonSlot.start_time >= current_time_utc
    ).all()

    slots_dict = [{
        'id': slot.id,
        'time': slot.start_time.replace(tzinfo=timezone.utc).astimezone(user_timezone).strftime('%Y-%m-%d %I:%M %p'),
        'teacher': slot.teacher.username
    } for slot in slots]

    return slots_dict
