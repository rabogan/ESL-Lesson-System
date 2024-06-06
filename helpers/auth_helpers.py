# teacher_helpers.py
from database import db
from flask_login import login_user
from flask import session
from models import StudentProfile, TeacherProfile
from werkzeug.security import generate_password_hash, check_password_hash

def is_username_taken(model, username):
    return model.query.filter_by(username=username).first() is not None

def create_user(model, username, email, password):
    hashed_password = generate_password_hash(password)
    new_user = model(username=username, email=email, password=hashed_password)
    db.session.add(new_user)
    db.session.commit()
    return new_user

def create_profile(model, user_id, image_file):
    if model == TeacherProfile:
        profile = model(teacher_id=user_id, image_file=image_file)
    elif model == StudentProfile:
        profile = model(student_id=user_id, image_file=image_file)
    db.session.add(profile)
    db.session.commit()
    return profile

def login_new_user(user, user_type):
    login_user(user)
    session['user_id'] = user.id
    session['user_type'] = user_type
    session['user_name'] = user.username

def authenticate_user(model, username, password):
    user = model.query.filter_by(username=username).first()
    if user and check_password_hash(user.password, password):
        return user
    return None