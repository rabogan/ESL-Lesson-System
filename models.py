from datetime import datetime
from flask_login import UserMixin
from database import db
from sqlalchemy.orm import backref


class User(UserMixin):
    """
    User class that provides default implementations for user authentication.
    """    
    def __init__(self, id):
        self.id = id


class Student(db.Model, UserMixin):
    """
    Represents a student in the system.
    """    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(20), unique=True, nullable=False)
    password = db.Column(db.String(60), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    number_of_lessons = db.Column(db.Integer, default=0)
    lessons_purchased = db.Column(db.Integer, default=30)
    timezone = db.Column(db.String(50), default='America/Los_Angeles')
    profile = db.relationship('StudentProfile', uselist=False, back_populates='student')
    lesson_records = db.relationship('LessonRecord', back_populates='student')
    bookings = db.relationship('Booking', back_populates='student')

    @property
    def remaining_lessons(self):
        """
        Calculate remaining lessons based on purchased and used lessons.
        """        
        return self.lessons_purchased - self.number_of_lessons

    def __repr__(self):
        return f"Student('{self.username}', '{self.email}', '{self.number_of_lessons}')"


class StudentProfile(db.Model):
    """
    Represents a student's profile information.
    """
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


class Teacher(db.Model, UserMixin):
    """
    Represents a teacher in the system.
    """    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(20), unique=True, nullable=False)
    password = db.Column(db.String(60), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    timezone = db.Column(db.String(50), default='America/Los_Angeles')
    profile = db.relationship('TeacherProfile', uselist=False, back_populates='teacher')
    lesson_records = db.relationship('LessonRecord', back_populates='teacher')
    lesson_slots = db.relationship('LessonSlot', back_populates='teacher')

    def __repr__(self):
        return f"Teacher('{self.username}', '{self.email}')"


class TeacherProfile(db.Model):
    """
    Represents a teacher's profile information.
    """    
    id = db.Column(db.Integer, primary_key=True)
    age = db.Column(db.Integer)
    hobbies = db.Column(db.String(500))
    motto = db.Column(db.String(500))
    blood_type = db.Column(db.String(3))
    image_file = db.Column(db.String(20), nullable=False, default='default.jpg')
    teacher_id = db.Column(db.Integer, db.ForeignKey('teacher.id'))
    teacher = db.relationship('Teacher', back_populates='profile')

    def __repr__(self):
        return f"TeacherProfile('{self.age}', '{self.hobbies}', '{self.motto}', '{self.blood_type}', '{self.image_file}')"


class LessonRecord(db.Model):
    """
    Represents a record of a lesson between a student and a teacher.
    """    
    __tablename__ = 'lesson_record'
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('student.id'))
    teacher_id = db.Column(db.Integer, db.ForeignKey('teacher.id'))
    lesson_slot_id = db.Column(db.Integer, db.ForeignKey('lesson_slot.id'), nullable=False)
    strengths = db.Column(db.String(1000))
    areas_to_improve = db.Column(db.String(1000))
    new_words = db.relationship('Word', backref='lesson_record', cascade="all, delete-orphan")
    new_phrases = db.relationship('Phrase', backref='lesson_record', cascade="all, delete-orphan")
    lesson_summary = db.Column(db.String(1000))
    lastEditTime = db.Column(db.DateTime, default=datetime.utcnow)
    student = db.relationship('Student', back_populates='lesson_records')
    teacher = db.relationship('Teacher', back_populates='lesson_records')
    lesson_slot = db.relationship('LessonSlot', back_populates='lesson_records')
    booking = db.relationship('Booking', back_populates='lesson_record', uselist=False)

    def __repr__(self):
        return f"LessonRecord('{self.strengths}', '{self.areas_to_improve}', '{self.lesson_summary}', '{self.lastEditTime}')"


class Word(db.Model):
    """
    Represents a new word introduced in a lesson.
    """    
    __tablename__ = 'word'
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.String(100), nullable=False)
    lesson_record_id = db.Column(db.Integer, db.ForeignKey('lesson_record.id'))


class Phrase(db.Model):
    """
    Represents a new phrase introduced in a lesson.
    """    
    __tablename__ = 'phrase'
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.String(100), nullable=False)
    lesson_record_id = db.Column(db.Integer, db.ForeignKey('lesson_record.id'))

    
    
class LessonSlot(db.Model):
    """
    Represents a time slot available for lessons.
    """    
    __tablename__ = 'lesson_slot'
    id = db.Column(db.Integer, primary_key=True)
    teacher_id = db.Column(db.Integer, db.ForeignKey('teacher.id'), nullable=False)
    start_time = db.Column(db.DateTime, nullable=False, index=True)
    end_time = db.Column(db.DateTime, nullable=False)
    is_booked = db.Column(db.Boolean, default=False)
    teacher = db.relationship('Teacher', back_populates='lesson_slots')
    booking = db.relationship('Booking', uselist=False, back_populates='lesson_slot')
    lesson_records = db.relationship('LessonRecord', back_populates='lesson_slot')

    def __repr__(self):
        return f"LessonSlot('{self.teacher_id}', '{self.start_time}', '{self.end_time}', '{self.is_booked}')"


class Booking(db.Model):
    """
    Represents a booking of a lesson slot by a student.
    """    
    __tablename__ = 'booking'
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('student.id'), nullable=False)
    lesson_slot_id = db.Column(db.Integer, db.ForeignKey('lesson_slot.id'), nullable=False)
    lesson_record_id = db.Column(db.Integer, db.ForeignKey('lesson_record.id'), nullable=True)
    status = db.Column(db.String(20), nullable=False, default='booked')
    student = db.relationship('Student', back_populates='bookings')
    lesson_slot = db.relationship('LessonSlot', back_populates='booking')
    lesson_record = db.relationship('LessonRecord', back_populates='booking', uselist=False)

    def __repr__(self):
        return f"Booking('{self.student_id}', '{self.lesson_slot_id}', '{self.status}', '{self.lesson_record_id}')"