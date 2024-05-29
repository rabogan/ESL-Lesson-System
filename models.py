from datetime import datetime
import json
from flask_login import UserMixin
from sqlalchemy import types
from app import db

# Student model
class Student(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(20), unique=True, nullable=False)
    password = db.Column(db.String(60), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    number_of_lessons = db.Column(db.Integer, default=0)
    profile = db.relationship('StudentProfile', uselist=False, back_populates='student')
    lesson_records = db.relationship('LessonRecord', back_populates='student')
    bookings = db.relationship('Booking', back_populates='student')

    def __repr__(self):
        return f"Student('{self.username}', '{self.email}', '{self.number_of_lessons}')"


# StudentProfile model
class StudentProfile(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    hometown = db.Column(db.String(500))
    goal = db.Column(db.String(500))
    hobbies = db.Column(db.String(500))
    correction_style = db.Column(db.String(500))
    english_weakness = db.Column(db.String(500))
    image_file = db.Column(db.String(20), nullable=False, default='default1.png')
    student_id = db.Column(db.Integer, db.ForeignKey('student.id'))
    student = db.relationship('Student', back_populates='profile')

    def __repr__(self):
        return f"StudentProfile('{self.hometown}', '{self.goal}', '{self.hobbies}', '{self.correction_style}', '{self.english_weakness}', '{self.image_file}')"


# Teacher model
class Teacher(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(20), unique=True, nullable=False)
    password = db.Column(db.String(60), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    profile = db.relationship('TeacherProfile', uselist=False, back_populates='teacher')
    lesson_records = db.relationship('LessonRecord', back_populates='teacher')
    lesson_slots = db.relationship('LessonSlot', back_populates='teacher')  # new line

    def __repr__(self):
        return f"Teacher('{self.username}', '{self.email}')"


# TeacherProfile model
class TeacherProfile(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    age = db.Column(db.Integer)
    hobbies = db.Column(db.String(500))
    motto = db.Column(db.String(500))
    blood_type = db.Column(db.String(3))
    image_file = db.Column(db.String(20), nullable=False, default='default.jpg')
    teacher_id = db.Column(db.Integer, db.ForeignKey('teacher.id'))
    teacher = db.relationship('Teacher', back_populates='profile')

def __repr__(self):
    return f"TeacherProfile('{self.age}', '{self.hobbies}', '{self.motto}', '{self.blood_type}', '{self.image_file}', '{self.from_location}')"


# Since I'm not using ProgreSQL, I need to create a custom type to store JSON data in SQLite
class JsonEncodedDict(types.TypeDecorator):
    impl = types.String

    def process_bind_param(self, value, dialect):
        if value is None:
            return '{}'
        else:
            return json.dumps(value)

    def process_result_value(self, value, dialect):
        if value is None:
            return {}
        else:
            return json.loads(value)


# LessonRecord model
class LessonRecord(db.Model):
    __tablename__ = 'lesson_record'
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('student.id'))
    teacher_id = db.Column(db.Integer, db.ForeignKey('teacher.id'))
    strengths = db.Column(db.String(1000))
    areas_to_improve = db.Column(db.String(1000))
    new_words = db.Column(JsonEncodedDict)
    new_phrases = db.Column(JsonEncodedDict)
    lesson_summary = db.Column(db.String(1000))
    date = db.Column(db.DateTime, default=datetime.utcnow)

    student = db.relationship('Student', back_populates='lesson_records')
    teacher = db.relationship('Teacher', back_populates='lesson_records')

    def __repr__(self):
        return f"LessonRecord('{self.strengths}', '{self.areas_to_improve}', '{self.lesson_summary}')"


# Example of adding a lesson record (for future use!)
# new_lesson = LessonRecord(
#    student_id=1,
#    teacher_id=2,
#    strengths="Great pronunciation",
#    areas_to_improve="Needs to work on grammar",
#    new_words=["bureaucracy", "food truck", "grief"],
#    new_phrases=["I suck at English", "My family is ashamed of my idiocy", "Think positive!"],
#    lesson_summary="Great lesson focusing on shopping phrases."
#)
#db.session.add(new_lesson)
#db.session.commit()


# Representing the time slot that a teacher is available for a lesson
class LessonSlot(db.Model):
    __tablename__ = 'lesson_slot'
    id = db.Column(db.Integer, primary_key=True)
    teacher_id = db.Column(db.Integer, db.ForeignKey('teacher.id'), nullable=False)
    start_time = db.Column(db.DateTime, nullable=False)
    end_time = db.Column(db.DateTime, nullable=False)
    is_booked = db.Column(db.Boolean, default=False)
    teacher = db.relationship('Teacher', back_populates='lesson_slots')
    booking = db.relationship('Booking', uselist=False, back_populates='lesson_slot')

    def __repr__(self):
        return f"LessonSlot('{self.teacher_id}', '{self.start_time}', '{self.end_time}', '{self.is_booked}')"


# Not completed yet!
class Booking(db.Model):
    __tablename__ = 'booking'
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('student.id'), nullable=False)
    lesson_slot_id = db.Column(db.Integer, db.ForeignKey('lesson_slot.id'), nullable=False)
    status = db.Column(db.String(20), nullable=False, default='booked')
    student = db.relationship('Student', back_populates='bookings')
    lesson_slot = db.relationship('LessonSlot', back_populates='booking')

    def __repr__(self):
        return f"Booking('{self.student_id}', '{self.lesson_slot_id}', '{self.status}')"
