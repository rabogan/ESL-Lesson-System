# helpers/teacher_helpers.py
from database import db
from datetime import datetime, timezone
from sqlalchemy.orm import joinedload
from sqlalchemy import and_
from helpers.file_helpers import save_image_file
from helpers.time_helpers import ensure_timezone_aware
from models import Teacher, TeacherProfile, LessonRecord, LessonSlot, Student, Booking

def get_teacher_by_id(teacher_id):
    return db.session.query(Teacher).filter(Teacher.id == teacher_id).first()

def get_teacher_profile_by_id(teacher_id):
    return db.session.query(TeacherProfile).filter(TeacherProfile.teacher_id == teacher_id).first()

def update_teacher_profile(profile, form):
    """
    Update the teacher's profile with data from the form.
    """
    profile.age = form.age.data if form.age.data else None
    profile.hobbies = form.hobbies.data.strip() if form.hobbies.data else ''
    profile.motto = form.motto.data.strip() if form.motto.data else ''
    profile.blood_type = form.blood_type.data.strip() if form.blood_type.data else ''

    # Handle the image file separately because it's not a simple text field.
    if form.image_file.data:
        profile.image_file = save_image_file(form.image_file.data)

    db.session.commit()

def get_most_recent_lesson_record(teacher_id, timezone_str):
    most_recent_record = LessonRecord.query.filter(
        and_(
            LessonRecord.teacher_id == teacher_id,
            LessonRecord.lastEditTime <= datetime.now(timezone.utc),
            LessonRecord.lesson_summary.isnot(None)
        )
    ).options(
        joinedload(LessonRecord.student).joinedload(Student.profile)
    ).order_by(LessonRecord.lastEditTime.desc()).first()

    if most_recent_record:
        most_recent_record.lastEditTime = ensure_timezone_aware(most_recent_record.lastEditTime, timezone_str)
        most_recent_record.lesson_slot.start_time = ensure_timezone_aware(most_recent_record.lesson_slot.start_time, timezone_str)

    return most_recent_record

def get_upcoming_lessons(teacher_id, timezone_str):
    upcoming_lessons = LessonSlot.query.filter(
        and_(
            LessonSlot.teacher_id == teacher_id,
            LessonSlot.start_time >= datetime.now(timezone.utc),
            LessonSlot.is_booked == True
        )
    ).options(
        joinedload(LessonSlot.booking).joinedload(Booking.student).joinedload(Student.profile)
    ).order_by(LessonSlot.start_time.asc()).all()

    for lesson in upcoming_lessons:
        lesson.start_time = ensure_timezone_aware(lesson.start_time, timezone_str)

    return upcoming_lessons

def get_outstanding_lessons(teacher_id, timezone_str):
    outstanding_lessons = LessonRecord.query.filter(
        and_(
            LessonRecord.teacher_id == teacher_id,
            LessonRecord.lesson_summary == None
        )
    ).options(
        joinedload(LessonRecord.student).joinedload(Student.profile),
        joinedload(LessonRecord.lesson_slot)
    ).join(LessonSlot, LessonRecord.lesson_slot_id == LessonSlot.id).order_by(LessonSlot.start_time.asc()).all()

    for lesson in outstanding_lessons:
        lesson.lesson_slot.start_time = ensure_timezone_aware(lesson.lesson_slot.start_time, timezone_str)

    return outstanding_lessons