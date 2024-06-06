from models import LessonRecord, Teacher
from database import db
from helpers.time_helpers import convert_to_utc
from helpers.form_helpers import process_form_data
import json
from datetime import datetime, timezone

def get_lesson_by_id(lesson_id):
    """
    Fetch the lesson by its ID.
    """
    return db.session.query(LessonRecord).get(lesson_id)

def initialize_lesson_form(form, lesson):
    """
    Initialize the lesson form with the lesson data.
    """
    form.new_words.data = json.dumps(lesson.new_words)
    form.new_phrases.data = json.dumps(lesson.new_phrases)

def update_lesson_from_form(lesson, form):
    """
    Update the lesson record with data from the form.
    """
    lesson.lesson_summary = form.lesson_summary.data
    lesson.strengths = form.strengths.data
    lesson.areas_to_improve = form.areas_to_improve.data
    lesson.new_words = process_form_data(form.new_words.data)
    lesson.new_phrases = process_form_data(form.new_phrases.data)

def update_last_edit_time(lesson, teacher_id):
    """
    Update the last edit time of the lesson to the current time in the teacher's timezone.
    """
    teacher = db.session.get(Teacher, teacher_id)
    if teacher is None:
        raise ValueError(f"Teacher with ID {teacher_id} not found.")
    lesson.lastEditTime = convert_to_utc(datetime.now(timezone.utc), teacher.timezone)
