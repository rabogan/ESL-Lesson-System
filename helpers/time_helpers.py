import pytz
from datetime import datetime, timedelta, timezone

def get_user_timezone(timezone_str):
    """Fetch a valid timezone for the user, defaulting to 'America/Los_Angeles' if invalid."""
    try:
        return pytz.timezone(timezone_str)
    except pytz.UnknownTimeZoneError:
        return pytz.timezone('America/Los_Angeles')
    

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

def convert_to_utc(dt, timezone):
    dt = ensure_timezone_aware(dt, timezone)
    return dt.astimezone(pytz.utc)

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