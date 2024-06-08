# teacher_helpers.py
from database import db
from flask_login import login_user
from flask import session
from models import StudentProfile, TeacherProfile, Teacher, Student
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

def register_user(form, user_type):
    username = form.username.data
    email = form.email.data
    password = form.password.data

    if user_type == 'teacher':
        if is_username_taken(Teacher, username) or is_username_taken(Teacher, email):
            return None, "Username or email already exists"
        new_user = create_user(Teacher, username, email, password)
        create_profile(TeacherProfile, new_user.id, 'default.jpg')
    elif user_type == 'student':
        if is_username_taken(Student, username):
            return None, "Username already exists"
        new_user = create_user(Student, username, email, password)
        create_profile(StudentProfile, new_user.id, 'default1.jpg')

    login_new_user(new_user, user_type)
    return new_user, None

def login_user_helper(form, model, user_type):
    username = form.username.data
    password = form.password.data
    remember = form.remember.data

    if not username or not password:
        return None, "Please provide a valid username and password"

    user = authenticate_user(model, username, password)
    if user is None:
        return None, "Invalid username or password"
    login_new_user(user, user_type)
    login_user(user, remember=remember)

    return user, None