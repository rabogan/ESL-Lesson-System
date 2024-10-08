# helpers/teacher_helpers.py
from database import db
from datetime import datetime, timezone
from sqlalchemy.orm import joinedload
from sqlalchemy import and_
from helpers.file_helpers import save_image_file
from helpers.time_helpers import ensure_timezone_aware
from models import Teacher, TeacherProfile, LessonRecord, LessonSlot, Student, Booking


def get_teacher_by_id(teacher_id):
    """
    Retrieve a teacher by their ID.
    Created with help from ChatGPT
    Args:
        teacher_id (int): The ID of the teacher to retrieve.

    Returns:
        Teacher: The Teacher object if found, else None.
    """
    return db.session.query(Teacher).filter(Teacher.id == teacher_id).first()


def get_teacher_profile_by_id(teacher_id):
    """
    Retrieve a teacher's profile by the teacher's ID.
    Created with help from ChatGPT
    Args:
        teacher_id (int): The ID of the teacher whose profile to retrieve.

    Returns:
        TeacherProfile: The TeacherProfile object if found, else None.
    """
    return db.session.query(TeacherProfile).filter(TeacherProfile.teacher_id == teacher_id).first()


def update_teacher_profile(profile, form):
    """
    Update the teacher's profile with data from the form.
    Created with help from ChatGPT
    Args:
        profile (Profile): The teacher's profile to update.
        form (Form): The form containing updated profile data.
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
    """
    Retrieve the most recent lesson record for a teacher.
    Query is based on the last edit time and the presence of a lesson summary.
    Created with help from ChatGPT!
    Args:
        teacher_id (int): The ID of the teacher.
        timezone_str (str): The timezone string to make times timezone aware.

    Returns:
        LessonRecord: The most recent lesson record if found, else None.
    """
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
    """
    Retrieve upcoming lessons for a teacher.
    Created with help from ChatGPT
    Args:
        teacher_id (int): The ID of the teacher.
        timezone_str (str): The timezone string to make times timezone aware.

    Returns:
        list: A list of upcoming LessonSlot objects.
    """
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
    """
    Retrieve outstanding lessons for a teacher that have not been summarized.
    Created with help from ChatGPT
    Args:
        teacher_id (int): The ID of the teacher.
        timezone_str (str): The timezone string to make times timezone aware.

    Returns:
        list: A list of outstanding LessonRecord objects.
    """
    outstanding_lessons = LessonRecord.query.filter(
        and_(
            LessonRecord.teacher_id == teacher_id,
            LessonRecord.lesson_summary == None,
            LessonRecord.lesson_slot.has(LessonSlot.start_time <= datetime.now(timezone.utc))
        )
    ).options(
        joinedload(LessonRecord.student).joinedload(Student.profile),
        joinedload(LessonRecord.lesson_slot)
    ).join(LessonSlot, LessonRecord.lesson_slot_id == LessonSlot.id).order_by(LessonSlot.start_time.asc()).all()

    for lesson in outstanding_lessons:
        lesson.lesson_slot.start_time = ensure_timezone_aware(lesson.lesson_slot.start_time, timezone_str)

    return outstanding_lessons


def update_student_profile_from_form(student_profile, form):
    """
    Update the student's profile with data from the form.
    Created with help from ChatGPT
    Args:
        student_profile (StudentProfile): The student's profile object.
        form (TeacherEditsStudentForm): The form with updated data.

    Returns:
        bool: Whether the update was successful.
    """
    try:
        student_profile.hometown = form.hometown.data.strip() if form.hometown.data else ''
        student_profile.goal = form.goal.data.strip() if form.goal.data else ''
        student_profile.hobbies = form.hobbies.data.strip() if form.hobbies.data else ''
        student_profile.correction_style = form.correction_style.data.strip() if form.correction_style.data else ''
        student_profile.english_weakness = form.english_weakness.data.strip() if form.english_weakness.data else ''
        db.session.commit()
        return True
    except Exception as e:
        db.session.rollback()
        return False