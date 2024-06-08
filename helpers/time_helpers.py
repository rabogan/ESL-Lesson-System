import pytz
from datetime import datetime, timedelta, timezone


def get_user_timezone(timezone_str):
    """
    Fetch a valid timezone for the user, defaulting to 'America/Los_Angeles' if invalid.

    Args:
        timezone_str (str): The timezone string to fetch.

    Returns:
        timezone: The valid timezone object.
    """
    try:
        return pytz.timezone(timezone_str)
    except pytz.UnknownTimeZoneError:
        return pytz.timezone('America/Los_Angeles')
    

def ensure_timezone_aware(dt, timezone_str):
    """
    Ensure a datetime object is timezone-aware.

    If the datetime object is not timezone-aware, it will be converted to the specified
    timezone of the teacher/student.

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


def get_week_boundaries(user_timezone_str, week_offset=0):
    """
    Get the start and end of the week in the user's timezone.

    Args:
        user_timezone_str (str): The user's timezone string.
        week_offset (int, optional): The number of weeks to offset. Defaults to 0.

    Returns:
        tuple: The start and end of the week as UTC datetime objects.
    """
    user_timezone = pytz.timezone(user_timezone_str)
    today = datetime.now(timezone.utc).astimezone(user_timezone)
    
    # Calculate the start and end of the current week in the user's timezone
    start_of_week = today - timedelta(days=today.weekday(), hours=today.hour, minutes=today.minute, seconds=today.second, microseconds=today.microsecond) + timedelta(weeks=week_offset)
    end_of_week = start_of_week + timedelta(days=6, hours=23, minutes=59, seconds=59)
    start_of_week_utc = start_of_week.astimezone(timezone.utc)
    end_of_week_utc = end_of_week.astimezone(timezone.utc)

    return start_of_week_utc, end_of_week_utc