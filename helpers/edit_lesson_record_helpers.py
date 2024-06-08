from models import LessonRecord, Teacher, Word, Phrase
from forms import WordForm, PhraseForm
from database import db
from helpers.time_helpers import convert_to_utc
from datetime import datetime, timezone


def get_lesson_by_id(lesson_id):
    """
    Fetch the lesson by its ID.

    Args:
        lesson_id (int): The ID of the lesson to fetch.

    Returns:
        LessonRecord: The lesson record if found, else None.
    """
    return db.session.query(LessonRecord).get(lesson_id)


def initialize_lesson_form(form, lesson):
    """
    Initialize the lesson form with the lesson data.
    Created with help from ChatGPT
    Initialize the lesson form with the lesson data.

    Args:
        form (Form): The form to initialize.
        lesson (LessonRecord): The lesson record to populate the form with.
    """
    form.lesson_summary.data = lesson.lesson_summary
    form.strengths.data = lesson.strengths
    form.areas_to_improve.data = lesson.areas_to_improve

    for word in lesson.new_words:
        word_form = WordForm()
        word_form.content.data = word.content
        form.new_words.append_entry(word_form)

    for phrase in lesson.new_phrases:
        phrase_form = PhraseForm()
        phrase_form.content.data = phrase.content
        form.new_phrases.append_entry(phrase_form)


def update_lesson_from_form(lesson, form):
    """
    Update the lesson record with data from the form.
    Created with help from ChatGPT
    Args:
        lesson (LessonRecord): The lesson record to update.
        form (Form): The form containing the updated data.
    """
    lesson.lesson_summary = form.lesson_summary.data
    lesson.strengths = form.strengths.data
    lesson.areas_to_improve = form.areas_to_improve.data

    # Clear the existing words and phrases
    lesson.new_words.clear()
    lesson.new_phrases.clear()

    # Add new words and phrases from the form
    for word_form in form.new_words:
        if word_form.content.data:
            word = Word(content=word_form.content.data, lesson_record_id=lesson.id)
            lesson.new_words.append(word)

    for phrase_form in form.new_phrases:
        if phrase_form.content.data:
            phrase = Phrase(content=phrase_form.content.data, lesson_record_id=lesson.id)
            lesson.new_phrases.append(phrase)


def update_last_edit_time(lesson, teacher_id):
    """
    Update the last edit time of the lesson to the current time in the teacher's timezone.
    Created with help from ChatGPT
    Args:
        lesson (LessonRecord): The lesson record to update.
        teacher_id (int): The ID of the teacher performing the update.

    Raises:
        ValueError: If the teacher is not found.
    """
    teacher = db.session.get(Teacher, teacher_id)
    if teacher is None:
        raise ValueError(f"Teacher with ID {teacher_id} not found.")
    lesson.lastEditTime = convert_to_utc(datetime.now(timezone.utc), teacher.timezone)
