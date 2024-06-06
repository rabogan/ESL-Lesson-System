
from flask_wtf import FlaskForm
from flask_wtf.file import FileAllowed
from wtforms import ValidationError, SelectField, DateTimeField, StringField, PasswordField, SubmitField, BooleanField, HiddenField, IntegerField, FileField, TextAreaField
from wtforms.validators import DataRequired, Length, Email, EqualTo, Optional, NumberRange, InputRequired
import json
from wtforms import ValidationError
from models import Student, Teacher, LessonSlot
from helpers.form_helpers import strip_whitespace

class FileMaxSizeMB(object):
    def __init__(self, max_size_mb):
        self.max_size_mb = max_size_mb

    def __call__(self, form, field):
        file_size = len(field.data.read())
        field.data.seek(0)  # Reset file pointer to beginning
        if file_size > self.max_size_mb * 1024 * 1024:
            raise ValidationError(f'File size must be less than {self.max_size_mb}MB')
        

class RegistrationForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(min=2, max=20)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    confirmation = PasswordField('Confirm Password', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Register')

    def validate_username(self, username):
        user = Student.query.filter_by(username=username.data).first()
        if user:
            raise ValidationError('That username is taken. Please choose a different one.')
        
        teacher = Teacher.query.filter_by(username=username.data).first()
        if teacher:
            raise ValidationError('That username is taken by a teacher. Please choose a different one.')

    def validate_email(self, email):
        user = Student.query.filter_by(email=email.data).first()
        if user:
            raise ValidationError('That email is taken. Please choose a different one.')

        teacher = Teacher.query.filter_by(email=email.data).first()
        if teacher:
            raise ValidationError('That email is taken by a teacher. Please choose a different one.')

class LoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(min=2, max=20)])
    password = PasswordField('Password', validators=[DataRequired()])
    remember = BooleanField('Remember Me')
    submit = SubmitField('Login')

class EditTeacherProfileForm(FlaskForm):
    age = IntegerField('Age', validators=[Optional(), NumberRange(min=0)])
    hobbies = StringField('Hobbies', validators=[Optional(), Length(max=500), strip_whitespace])
    motto = StringField('Motto', validators=[Optional(), Length(max=500), strip_whitespace])
    blood_type = StringField('Blood Type', validators=[Optional(), Length(max=5), strip_whitespace])
    image_file = FileField('Profile Image', validators=[Optional(), FileAllowed(['jpg', 'png', 'gif', 'jpeg']), FileMaxSizeMB(5)])
    submit = SubmitField('Update Profile')

class StudentProfileForm(FlaskForm):
    hometown = StringField('Hometown', validators=[Optional(), Length(max=500), strip_whitespace])
    goal = StringField('Goal', validators=[Optional(), Length(max=1000), strip_whitespace])
    hobbies = StringField('Hobbies', validators=[Optional(), Length(max=1000), strip_whitespace])
    correction_style = StringField('Correction Style', validators=[Optional(), Length(max=1000), strip_whitespace])
    english_weakness = StringField('English Weakness', validators=[Optional(), Length(max=1000), strip_whitespace])
    image_file = FileField('Profile Image', validators=[Optional(), FileAllowed(['jpg', 'png', 'gif', 'jpeg']), FileMaxSizeMB(5)])
    submit = SubmitField('Update Profile')

class TeacherEditsStudentForm(FlaskForm):
    hometown = StringField('Hometown', validators=[Optional(), Length(max=500), strip_whitespace])
    goal = StringField('Goal', validators=[Optional(), Length(max=1000), strip_whitespace])
    hobbies = StringField('Hobbies', validators=[Optional(), Length(max=1000), strip_whitespace])
    correction_style = StringField('Correction Style', validators=[Optional(), Length(max=1000), strip_whitespace])
    english_weakness = StringField('English Weakness', validators=[Optional(), Length(max=1000), strip_whitespace])
    submit = SubmitField('Update Profile')

class LessonRecordForm(FlaskForm):
    csrf_token = HiddenField('CSRF Token', validators=[InputRequired()])
    lesson_summary = TextAreaField('Lesson Summary', validators=[Optional()])
    strengths = TextAreaField('Strengths', validators=[Optional()])
    areas_to_improve = TextAreaField('Areas to Improve', validators=[Optional()])
    new_words = HiddenField('New Words', default='[]', validators=[Optional()])
    new_phrases = HiddenField('New Phrases', default='[]', validators=[Optional()])
    submit = SubmitField('Update Lesson')

    def validate_new_words(form, field):
        if field.data and field.data != '[]':
            try:
                words = json.loads(field.data)
                for word in words:
                    if not isinstance(word, str):
                        raise ValidationError('Each word must be a string.')
            except json.JSONDecodeError:
                raise ValidationError('Invalid JSON data for new_words.')

    def validate_new_phrases(form, field):
        if field.data and field.data != '[]':
            try:
                phrases = json.loads(field.data)
                for phrase in phrases:
                    if not isinstance(phrase, str):
                        raise ValidationError('Each phrase must be a string.')
            except json.JSONDecodeError:
                raise ValidationError('Invalid JSON data for new_phrases.')

    def validate(self, extra_validators=None):
        rv = FlaskForm.validate(self)
        if not rv:
            return False
        if self.new_words.data == '[]' and self.new_phrases.data == '[]':
            self.new_words.errors.append('At least one of New Words or New Phrases must be filled.')
            return False
        return True

class LessonSlotsForm(FlaskForm):
    start_time = DateTimeField('Start Time', validators=[DataRequired()])
    end_time = DateTimeField('End Time', validators=[DataRequired()])
    is_booked = BooleanField('Is Booked', default=False)
    submit = SubmitField('Submit')

class StudentLessonSlotForm(FlaskForm):
    teacher = SelectField('Teacher', coerce=int, validators=[DataRequired()])
    lesson_slot = SelectField('Lesson Slot', coerce=int, validators=[DataRequired()])
    submit = SubmitField('Submit')

class CancelLessonForm(FlaskForm):
    lesson_id = HiddenField('Lesson ID', validators=[DataRequired()])
    csrf_token = HiddenField()

    def validate_lesson_id(self, lesson_id):
        lesson = LessonSlot.query.get(lesson_id.data)
        if not lesson:
            raise ValidationError('Invalid lesson ID.')

    def validate_on_submit(self):
        if not super().validate_on_submit():
            return False
        return True