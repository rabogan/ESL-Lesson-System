# dashboard_helpers.py
from datetime import datetime, timezone
from sqlalchemy.orm import joinedload
from models import LessonRecord, LessonSlot, Booking, Student, Teacher
from helpers.time_helpers import ensure_timezone_aware


def get_most_recent_lesson_record(user_id, user_type, timezone_str):
    """
    Retrieve the most recent lesson record for the given user.
    Created with help from ChatGPT
    Args:
        user_id (int): The ID of the user (student or teacher).
        user_type (str): The type of the user ('student' or 'teacher').
        timezone_str (str): The timezone string to make times timezone aware.

    Returns:
        LessonRecord: The most recent lesson record.
    """
    if user_type == 'student':
        most_recent_record = LessonRecord.query.filter(
            LessonRecord.student_id == user_id,
            LessonRecord.lesson_slot.has(LessonSlot.start_time <= datetime.now(timezone.utc))
        ).options(
            joinedload(LessonRecord.teacher).joinedload(Teacher.profile),
            joinedload(LessonRecord.lesson_slot),
            joinedload(LessonRecord.new_words),
            joinedload(LessonRecord.new_phrases) 
        ).order_by(LessonRecord.lastEditTime.desc()).first()
    elif user_type == 'teacher':
        most_recent_record = LessonRecord.query.filter(
            LessonRecord.teacher_id == user_id,
            LessonRecord.lesson_slot.has(LessonSlot.start_time <= datetime.now(timezone.utc))
        ).options(
            joinedload(LessonRecord.student).joinedload(Student.profile),
            joinedload(LessonRecord.lesson_slot),
            joinedload(LessonRecord.new_words),
            joinedload(LessonRecord.new_phrases) 
        ).order_by(LessonRecord.lastEditTime.desc()).first()
    
    if most_recent_record:
        most_recent_record.lastEditTime = ensure_timezone_aware(most_recent_record.lastEditTime, timezone_str)
        if most_recent_record.lesson_slot and most_recent_record.lesson_slot.start_time:
            most_recent_record.lesson_slot.start_time = ensure_timezone_aware(most_recent_record.lesson_slot.start_time, timezone_str)
    
    return most_recent_record


def get_upcoming_lessons(user_id, user_type, timezone_str):
    """
    Retrieve the upcoming lessons for the given user.
    Created with help from ChatGPT
    Args:
        user_id (int): The ID of the user (student or teacher).
        user_type (str): The type of the user ('student' or 'teacher').
        timezone_str (str): The timezone string to make times timezone aware.

    Returns:
        list: A list of upcoming LessonSlot objects.
    """
    if user_type == 'student':
        upcoming_lessons = LessonSlot.query.join(Booking).filter(
            Booking.student_id == user_id,
            LessonSlot.start_time >= datetime.now(timezone.utc)
        ).options(
            joinedload(LessonSlot.teacher).joinedload(Teacher.profile)
        ).order_by(LessonSlot.start_time.asc()).all()
    elif user_type == 'teacher':
        upcoming_lessons = LessonSlot.query.filter(
            LessonSlot.teacher_id == user_id,
            LessonSlot.start_time >= datetime.now(timezone.utc),
            LessonSlot.is_booked == True
        ).options(
            joinedload(LessonSlot.booking).joinedload(Booking.student).joinedload(Student.profile)
        ).order_by(LessonSlot.start_time.asc()).all()
    
    for lesson in upcoming_lessons:
        lesson.start_time = ensure_timezone_aware(lesson.start_time, timezone_str)
    
    return upcoming_lessons
