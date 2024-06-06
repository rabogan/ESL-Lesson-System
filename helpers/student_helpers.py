from models import Student
from database import db

def get_student_by_id(student_id):
    """Fetch a student by their ID."""
    return db.session.get(Student, student_id)

def update_student_profile(form, profile):
    """Update the student's profile with data from the form."""
    profile.hometown = form.hometown.data.strip() if form.hometown.data else ''
    profile.goal = form.goal.data.strip() if form.goal.data else ''
    profile.hobbies = form.hobbies.data.strip() if form.hobbies.data else ''
    profile.correction_style = form.correction_style.data.strip() if form.correction_style.data else ''
    profile.english_weakness = form.english_weakness.data.strip() if form.english_weakness.data else ''