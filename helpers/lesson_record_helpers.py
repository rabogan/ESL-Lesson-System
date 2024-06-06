from models import LessonRecord, LessonSlot, Student, Teacher
from pytz import timezone
from sqlalchemy.orm import joinedload
from datetime import datetime, timezone
from helpers.time_helpers import ensure_timezone_aware


def get_paginated_lesson_records(user_id, page, user_type):
    """Fetch paginated lesson records for the given user."""
    if user_type == 'student':
        query = LessonRecord.query.filter(
            LessonRecord.student_id == user_id,
            LessonRecord.lesson_slot.has(LessonSlot.start_time <= datetime.now(timezone.utc))
        ).options(
            joinedload(LessonRecord.teacher).joinedload(Teacher.profile),
            joinedload(LessonRecord.lesson_slot)
        )
    elif user_type == 'teacher':
        query = LessonRecord.query.join(LessonSlot).filter(
            LessonRecord.teacher_id == user_id,
            LessonSlot.start_time <= datetime.now(timezone.utc)
        ).options(
            joinedload(LessonRecord.student).joinedload(Student.profile)
        )
    return query.order_by(LessonRecord.lastEditTime.desc()).paginate(page=page, per_page=5)

def make_times_timezone_aware(lesson_records, timezone_str):
    """Make the lastEditTime and lesson slot start_time timezone-aware."""
    for record in lesson_records.items:
        record.lastEditTime = ensure_timezone_aware(record.lastEditTime, timezone_str)
        if record.lesson_slot and record.lesson_slot.start_time:
            record.lesson_slot.start_time = ensure_timezone_aware(record.lesson_slot.start_time, timezone_str)
    return lesson_records