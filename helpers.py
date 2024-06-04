import os
import secrets
from flask import current_app, session
from flask_login import current_user
from datetime import datetime, timedelta, timezone
import pytz


def save_image_file(image_file):
    # Generate a random hex for the filename to ensure it's unique
    random_hex = secrets.token_hex(8)
    _, file_extension = os.path.splitext(image_file.filename)
    new_filename = random_hex + file_extension

    # Determine the directory and default image based on the user type
    if session['user_type'] == 'teacher':
        directory = 'static/img/teacherImg'
        default_image = 'default.jpg'
    elif session['user_type'] == 'student':
        directory = 'static/img/studentImg'
        default_image = 'default1.jpg'
    else:
        return None  # Or handle this case differently

    # Build the full file path for the new image
    image_path = os.path.join(current_app.root_path, directory, new_filename)

    # Save the new image file
    image_file.save(image_path)

    # Only delete the old image if it's not the default image
    old_image_path = os.path.join(current_app.root_path, directory, current_user.profile.image_file)
    if current_user.profile.image_file != default_image and os.path.exists(old_image_path):
        try:
            os.remove(old_image_path)
        except PermissionError:
            pass  # Ignore the permission error

    return new_filename


def ensure_timezone_aware(dt, timezone_str):
    """
    Ensure a datetime object is timezone-aware.
    i.e. If the datetime object is not timezone-aware, 
    it will be converted to the specified timezone of the teacher/student.

    Args:
        dt (datetime): The datetime object to check.
        timezone_str (str): The timezone to use if dt is not timezone-aware.

    Returns:
        datetime: The timezone-aware datetime object.
    """
    user_timezone = pytz.timezone(timezone_str)
    if dt.tzinfo is None:
        dt = pytz.utc.localize(dt)
    return dt.astimezone(user_timezone)


# This is a WORKING way getting getting the start and end of the week in the user's timezone!
# Called using: start_of_week_utc, end_of_week_utc = get_start_end_of_week(student.timezone, week_offset)
# Used in book_lesson - can avoid DRY using it!
# This is a WORKING way getting getting the start and end of the week in the user's timezone!
# Called using: start_of_week_utc, end_of_week_utc = get_start_end_of_week(student.timezone, week_offset)
# Used in book_lesson - can avoid DRY using it!
def get_week_boundaries(user_timezone_str, week_offset=0):
    """_summary_

    Args:
        user_timezone_str (_type_): _description_
        week_offset (int, optional): _description_. Defaults to 0.

    Returns:
        _type_: _description_
    """
    user_timezone = pytz.timezone(user_timezone_str)
    today = datetime.now(timezone.utc).astimezone(user_timezone)
    
    # Calculate the start and end of the current week in the user's timezone
    start_of_week = today - timedelta(days=today.weekday(), hours=today.hour, minutes=today.minute, seconds=today.second, microseconds=today.microsecond) + timedelta(weeks=week_offset)
    end_of_week = start_of_week + timedelta(days=7)
    start_of_week_utc = start_of_week.astimezone(timezone.utc)
    end_of_week_utc = end_of_week.astimezone(timezone.utc)

    return start_of_week_utc, end_of_week_utc