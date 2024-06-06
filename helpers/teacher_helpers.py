# helpers/teacher_helpers.py
from database import db
from models import Teacher, TeacherProfile

def get_teacher_by_id(teacher_id):
    return db.session.query(Teacher).filter(Teacher.id == teacher_id).first()

def get_teacher_profile_by_id(teacher_id):
    return db.session.query(TeacherProfile).filter(TeacherProfile.teacher_id == teacher_id).first()
