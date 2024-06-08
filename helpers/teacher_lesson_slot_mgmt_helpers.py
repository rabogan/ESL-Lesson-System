from datetime import datetime
from database import db
import pytz
from models import LessonSlot
from helpers.time_helpers import ensure_timezone_aware


# Helper functions
def manage_slot(start_time_str, end_time_str, teacher_id, timezone_str, action):
    """
    Manage a lesson slot by opening or closing it.
    Query created with help from ChatGPT
    Args:
        start_time_str (str): The start time string in ISO format.
        end_time_str (str): The end time string in ISO format.
        teacher_id (int): The ID of the teacher.
        timezone_str (str): The timezone string.
        action (str): The action to perform ('open' or 'close').

    Returns:
        dict: A dictionary indicating success or error status.
    """
    local_start_time = datetime.strptime(start_time_str, '%Y-%m-%dT%H:%M')
    local_end_time = datetime.strptime(end_time_str, '%Y-%m-%dT%H:%M')

    timezone = pytz.timezone(timezone_str)
    start_time = timezone.localize(local_start_time).astimezone(pytz.UTC)
    end_time = timezone.localize(local_end_time).astimezone(pytz.UTC)

    existing_slot = LessonSlot.query.filter_by(teacher_id=teacher_id, start_time=start_time, end_time=end_time).first()

    if existing_slot and action == 'close':
        db.session.delete(existing_slot)
        return {'status': 'success', 'message': 'Lesson slot closed!'}
    elif not existing_slot and action == 'open':
        new_slot = LessonSlot(teacher_id=teacher_id, start_time=start_time, end_time=end_time)
        db.session.add(new_slot)
        return {'status': 'success', 'message': 'New lesson slot created!'}
    else:
        return {'status': 'error', 'message': 'Invalid action or lesson slot does not exist.'}
    
    
def get_lesson_slots_for_week(teacher_id, start_of_week_utc, end_of_week_utc):
    """
    Retrieve lesson slots for the given week.
    Query created with help from ChatGPT
    Args:
        teacher_id (int): The ID of the teacher.
        start_of_week_utc (datetime): The start of the week in UTC.
        end_of_week_utc (datetime): The end of the week in UTC.

    Returns:
        list: A list of LessonSlot objects for the week.
    """
    return LessonSlot.query.filter(
        LessonSlot.teacher_id == teacher_id,
        LessonSlot.start_time >= start_of_week_utc,
        LessonSlot.start_time <= end_of_week_utc
    ).all()
    
    
def open_slot(start_time, end_time, teacher_id, timezone):
    """
    Open a new lesson slot.
    Query created with help from ChatGPT
    Args:
        start_time (datetime): The start time of the slot.
        end_time (datetime): The end time of the slot.
        teacher_id (int): The ID of the teacher.
        timezone (timezone): The teacher's timezone.

    Returns:
        dict: A dictionary indicating success and the new slot ID.
    """
    start_time = ensure_timezone_aware(start_time, timezone).astimezone(pytz.UTC)
    end_time = ensure_timezone_aware(end_time, timezone).astimezone(pytz.UTC)
    new_slot = LessonSlot(teacher_id=teacher_id, start_time=start_time, end_time=end_time, is_booked=False)
    db.session.add(new_slot)
    db.session.commit()
    return {'status': 'success', 'slot_id': new_slot.id}


def close_slot(slot_id, teacher_id):
    """
    Close an existing lesson slot.
    Query created with help from ChatGPT
    Args:
        slot_id (int): The ID of the slot to close.
        teacher_id (int): The ID of the teacher.

    Returns:
        dict: A dictionary indicating success or error status.
    """
    slot = LessonSlot.query.get(slot_id)
    if slot and slot.teacher_id == teacher_id:
        db.session.delete(slot)
        db.session.commit()
        return {'status': 'success'}
    else:
        return {'status': 'error'}