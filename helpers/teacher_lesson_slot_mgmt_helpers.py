from datetime import datetime
from database import db
import pytz
from models import LessonSlot
from helpers.time_helpers import ensure_timezone_aware

# Helper functions
def manage_slot(start_time_str, end_time_str, teacher_id, timezone_str, action):
    # Convert the provided start and end time strings to datetime objects
    local_start_time = datetime.strptime(start_time_str, '%Y-%m-%dT%H:%M')
    local_end_time = datetime.strptime(end_time_str, '%Y-%m-%dT%H:%M')

    # Localize the times to the specified timezone and convert to UTC
    timezone = pytz.timezone(timezone_str)
    start_time = timezone.localize(local_start_time).astimezone(pytz.UTC)
    end_time = timezone.localize(local_end_time).astimezone(pytz.UTC)

    # Query for an existing slot with the same start and end times
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
    
    
def open_slot(start_time, end_time, teacher_id, timezone):
    start_time = ensure_timezone_aware(start_time, timezone).astimezone(pytz.UTC)
    end_time = ensure_timezone_aware(end_time, timezone).astimezone(pytz.UTC)
    new_slot = LessonSlot(teacher_id=teacher_id, start_time=start_time, end_time=end_time, is_booked=False)
    db.session.add(new_slot)
    db.session.commit()
    return {'status': 'success', 'slot_id': new_slot.id}

def close_slot(slot_id, teacher_id):
    slot = LessonSlot.query.get(slot_id)
    if slot and slot.teacher_id == teacher_id:
        db.session.delete(slot)
        db.session.commit()
        return {'status': 'success'}
    else:
        return {'status': 'error'}