import json
import pytz
import logging
from flask_limiter import Limiter
from helpers import save_image_file, ensure_timezone_aware, get_week_boundaries
from flask import Flask, session, render_template, request, redirect, url_for, flash, jsonify, abort
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import types, and_
from sqlalchemy.orm import joinedload
from flask_migrate import Migrate
from datetime import datetime, timedelta, timezone
from werkzeug.security import generate_password_hash, check_password_hash
from flask_wtf import FlaskForm, CSRFProtect
from flask_wtf.file import FileAllowed
from wtforms import ValidationError, SelectField, DateTimeField, StringField, PasswordField, SubmitField, BooleanField, HiddenField, IntegerField, FileField, TextAreaField, HiddenField
from wtforms.validators import DataRequired, Length, Email, EqualTo, Optional, NumberRange


# Initialize Flask app
app = Flask(__name__)
app.secret_key = 'coolie_killer_huimin_himitsunakotogawaruidesune'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///site.db'
app.config['DEBUG'] = True
app.logger.setLevel(logging.INFO)


# Initialize extensions
db = SQLAlchemy(app)
migrate = Migrate(app, db)
login_manager = LoginManager()
login_manager.init_app(app)
csrf = CSRFProtect(app)
csrf.init_app(app)
limiter = Limiter(app)


# Set up logging
logging.basicConfig(level=logging.DEBUG)


def strip_whitespace(form, field):
    if field.data:
        field.data = field.data.strip()


# Forms
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

    def validate_email(self, email):
        user = Student.query.filter_by(email=email.data).first()
        if user:
            raise ValidationError('That email is taken. Please choose a different one.')


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
    image_file = FileField('Profile Image', validators=[Optional(), FileAllowed(['jpg', 'png'])])
    submit = SubmitField('Update Profile')


class StudentProfileForm(FlaskForm):
    hometown = StringField('Hometown', validators=[Optional(), Length(max=500), strip_whitespace])
    goal = StringField('Goal', validators=[Optional(), Length(max=1000), strip_whitespace])
    hobbies = StringField('Hobbies', validators=[Optional(), Length(max=1000), strip_whitespace])
    correction_style = StringField('Correction Style', validators=[Optional(), Length(max=1000), strip_whitespace])
    english_weakness = StringField('English Weakness', validators=[Optional(), Length(max=1000), strip_whitespace])
    image_file = FileField('Profile Image', validators=[Optional(), FileAllowed(['jpg', 'png'])])
    submit = SubmitField('Update Profile')


class TeacherEditsStudentForm(FlaskForm):
    hometown = StringField('Hometown', validators=[Optional(), Length(max=500), strip_whitespace])
    goal = StringField('Goal', validators=[Optional(), Length(max=1000), strip_whitespace])
    hobbies = StringField('Hobbies', validators=[Optional(), Length(max=1000), strip_whitespace])
    correction_style = StringField('Correction Style', validators=[Optional(), Length(max=1000), strip_whitespace])
    english_weakness = StringField('English Weakness', validators=[Optional(), Length(max=1000), strip_whitespace])
    submit = SubmitField('Update Profile')
    

class LessonRecordForm(FlaskForm):
    lesson_summary = TextAreaField('Lesson Summary')
    strengths = TextAreaField('Strengths')
    areas_to_improve = TextAreaField('Areas to Improve')
    new_words = TextAreaField('New Words', validators=[Optional()])
    new_phrases = TextAreaField('New Phrases', validators=[Optional()])
    submit = SubmitField('Update Lesson')

    def validate_new_words(form, field):
        words = json.loads(field.data) if field.data else []
        if len(words) > 40:
            raise ValidationError('You can add a maximum of 40 new words.')

    def validate_new_phrases(form, field):
        phrases = json.loads(field.data) if field.data else []
        if len(phrases) > 20:
            raise ValidationError('You can add a maximum of 20 new phrases.')


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
            app.logger.debug(f"Validation errors: {self.errors}")
            return False
        app.logger.debug(f"Lesson ID in form: {self.lesson_id.data}")
        return True


# User model
class User(UserMixin):
    def __init__(self, id):
        self.id = id


# Student model
class Student(db.Model, UserMixin):
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
        return self.lessons_purchased - self.number_of_lessons

    def __repr__(self):
        return f"Student('{self.username}', '{self.email}', '{self.number_of_lessons}')"


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
    timezone = db.Column(db.String(50), default='America/Los_Angeles')
    profile = db.relationship('TeacherProfile', uselist=False, back_populates='teacher')
    lesson_records = db.relationship('LessonRecord', back_populates='teacher')
    lesson_slots = db.relationship('LessonSlot', back_populates='teacher')

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
    lesson_slot_id = db.Column(db.Integer, db.ForeignKey('lesson_slot.id'), nullable=False)
    strengths = db.Column(db.String(1000))
    areas_to_improve = db.Column(db.String(1000))
    new_words = db.Column(JsonEncodedDict)
    new_phrases = db.Column(JsonEncodedDict)
    lesson_summary = db.Column(db.String(1000))
    lastEditTime = db.Column(db.DateTime, default=datetime.utcnow)
    student = db.relationship('Student', back_populates='lesson_records')
    teacher = db.relationship('Teacher', back_populates='lesson_records')
    lesson_slot = db.relationship('LessonSlot', back_populates='lesson_records')
    booking = db.relationship('Booking', back_populates='lesson_record', uselist=False)

    def __repr__(self):
        return f"LessonRecord('{self.strengths}', '{self.areas_to_improve}', '{self.lesson_summary}', '{self.lastEditTime}')"


# Representing the time slot that a teacher is available for a lesson
class LessonSlot(db.Model):
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


# Ensure database tables are created
with app.app_context():
    # Ensure database tables are created
    db.create_all()
    print("Tables created")
        

# This handles whether a student or teacher is logging in
@login_manager.user_loader
def load_user(user_id):
    user_type = session.get('user_type')
    if user_type == 'student':
        return db.session.get(Student, int(user_id))
    elif user_type == 'teacher':
        return db.session.get(Teacher, int(user_id))
    else:
        return None


@app.errorhandler(404)
def page_not_found(e):
    return render_template('apology.html', top="404 Error", bottom="Page not found"), 404


@app.errorhandler(500)
def internal_error(error):
    app.logger.error(f"Server Error: {error}")
    return render_template('500.html'), 500

# Homepage Routes
@app.route("/")
def index():
    """
    Just the index page of the web app
    """
    return render_template("display.html")


@app.route('/meetYourTeacher')
def meet_your_teacher():
    """
    Shows a rogue's gallery of all the teachers in the system.
    """
    page = request.args.get('page', 1, type=int)
    teachers = Teacher.query.paginate(page=page, per_page=6)
    return render_template('meetYourTeacher.html', teachers=teachers)


class SimpleForm(FlaskForm):
    submit = SubmitField('Submit')

@app.route('/test_page')
def test_page():
    return render_template('minimal_test.html')


@app.route('/ourLessons')
def our_lessons():
    """
    This page provides information about the lessons offered.
    """
    return render_template('ourLessons.html')


@app.route('/contactSchool')
def contact_school():
    """
    This page provides contact information for the school.
    """
    return render_template('contactSchool.html')



@app.route('/teacher_profile/<int:teacher_id>', methods=['GET'])
def teacher_profile(teacher_id):
    """
    This route displays a teacher's profile.
    It is a public view and not editable.
    """
    # Fetch the teacher
    teacher = db.session.query(Teacher).filter(Teacher.id == teacher_id).first()
    if teacher is None:
        app.logger.error(f"Teacher with ID {teacher_id} not found.")
        return render_template('404.html'), 404

    # Fetch the teacher's profile
    profile = db.session.query(TeacherProfile).filter(TeacherProfile.teacher_id == teacher_id).first()
    if profile is None:
        app.logger.error(f"Profile for teacher with ID {teacher_id} not found.")
        return render_template('404.html'), 404

    # Pass the teacher's profile to the template
    return render_template('view_teacher_profile.html', teacher=teacher, profile=profile)



@app.route('/portal_choice')
def portal_choice():
    """
    This is where the user chooses whether to log in/register as a student or teacher.
    """
    return render_template('portal_choice.html')


@app.route("/student/register", methods=["GET", "POST"])
@limiter.limit("5/minute")
def student_register():
    """
    Register a new student here
    """
    form = RegistrationForm()
    
    if form.validate_on_submit():
        username = form.username.data
        email = form.email.data
        password = form.password.data

        # Check if the username already exists
        existing_student = Student.query.filter_by(username=username).first()
        if existing_student:
            form.username.errors.append("Username already exists")
            return render_template("student_register.html", form=form), 400

        hashed_password = generate_password_hash(password)
        new_student = Student(username=username, email=email, password=hashed_password)
        db.session.add(new_student)
        db.session.commit()
        
        # Create a new StudentProfile for the newly registered student
        profile = StudentProfile(student_id=new_student.id, image_file='default1.jpg')
        db.session.add(profile)
        db.session.commit()

        # Store the user_ID/user_type/user_name in the session
        session['user_id'] = new_student.id
        session['user_type'] = 'student'
        session['user_name'] = new_student.username 

        return redirect(url_for("student_login"))
    
    return render_template("student_register.html", form=form)


@app.route("/student/login", methods=["GET", "POST"])
@limiter.limit("5/minute")
def student_login():
    """
    Allow existing students to log in (or redirect them!)
    """
    form = LoginForm()
    if form.validate_on_submit():
        username = form.username.data
        password = form.password.data
        remember = form.remember.data

        # Check the validity of the input
        if not username or not password:
            return render_template("apology.html", top="Error", bottom="Please provide a valid username and password"), 400

        # Check if the username exists and the password is correct
        student = Student.query.filter_by(username=username).first()
        if student is None or not check_password_hash(student.password, password):
            return render_template("apology.html", top="Error", bottom="Invalid username or password"), 400

        # Log in the user and store their ID and type in the session
        login_user(student, remember=remember)
        session['user_id'] = student.id
        session['user_type'] = 'student'
        session['user_name'] = student.username

        return redirect(url_for("student_dashboard"))
    return render_template("student_login.html", form=form)


@app.route("/teacher/register", methods=["GET", "POST"])
@limiter.limit("5/minute")
def teacher_register():
    form = RegistrationForm()
    if form.validate_on_submit():
        hashed_password = generate_password_hash(form.password.data)
        new_teacher = Teacher(username=form.username.data, email=form.email.data, password=hashed_password)
        
        # Check if the username or email already exists
        existing_teacher = Teacher.query.filter((Teacher.username == form.username.data) | (Teacher.email == form.email.data)).first()
        if existing_teacher is not None:
            return render_template("apology.html", top="Error", bottom="Registration error"), 400


        db.session.add(new_teacher)
        db.session.commit()

        profile = TeacherProfile(teacher_id=new_teacher.id, image_file='default.jpg')
        db.session.add(profile)
        db.session.commit()

        login_user(new_teacher)  # Use Flask-Login to manage the session
        
        # Store the new teacher's info in the session
        session['user_id'] = new_teacher.id
        session['user_type'] = 'teacher'
        session['user_name'] = new_teacher.username

        return redirect(url_for("teacher_dashboard"))  # Redirect to a different page
    return render_template("teacher_register.html", form=form)


@app.route("/teacher/login", methods=["GET", "POST"])
@limiter.limit("5/minute")
def teacher_login():
    """
    Allow existing teachers to log in!
    """
    form = LoginForm()
    if form.validate_on_submit():
        username = form.username.data
        password = form.password.data
        remember = form.remember.data

        # Check the validity of the input
        if not username or not password:
            return render_template("apology.html", top="Error", bottom="Please provide a valid username and password"), 400

        # Check if the username exists and the password is correct
        teacher = Teacher.query.filter_by(username=username).first()
        if teacher is None or not check_password_hash(teacher.password, password):
            return render_template("apology.html", top="Error", bottom="Invalid username or password"), 400


        # Log in the user and store their info in the session
        login_user(teacher, remember=remember)
        session['user_id'] = teacher.id
        session['user_type'] = 'teacher'  # Add this line
        session['user_name'] = teacher.username  # If you need the username in the session

        return redirect(url_for("teacher_dashboard"))
    return render_template("teacher_login.html", form=form)


@app.route('/logout')
def logout():
    """
    Log out the user and clear the session
    """
    logout_user()
    session.pop('user_id', None)
    session.pop('user_type', None)
    flash('You were logged out')
    return redirect(url_for('index'))


# Teacher Only Routes
@app.route('/teacher/teacher_dashboard')
@login_required
def teacher_dashboard():
    # Ensure the current user is a teacher
    if session['user_type'] != 'teacher':
        return redirect(url_for('index'))

    # Fetch the most recent lesson record for the logged-in teacher
    most_recent_record = LessonRecord.query.filter(
        and_(
            LessonRecord.teacher_id == session['user_id'],
            LessonRecord.lastEditTime <= datetime.now(timezone.utc),
            LessonRecord.lesson_summary.isnot(None)
        )
    ).options(
        joinedload(LessonRecord.student).joinedload(Student.profile)
    ).order_by(LessonRecord.lastEditTime.desc()).first()

    # Fetch all upcoming booked lesson slots for the logged-in teacher
    upcoming_lessons = LessonSlot.query.filter(
        and_(
            LessonSlot.teacher_id == session['user_id'],
            LessonSlot.start_time >= datetime.now(timezone.utc),
            LessonSlot.is_booked == True
        )
    ).options(
        joinedload(LessonSlot.booking).joinedload(Booking.student).joinedload(Student.profile)
    ).order_by(LessonSlot.start_time.asc()).all()

    # Debugging: Print the upcoming lessons
    print(upcoming_lessons)

    # Convert lesson times to the teacher's timezone
    teacher = db.session.get(Teacher, session['user_id'])
    if teacher is None:
        app.logger.error(f"Teacher with ID {session['user_id']} not found.")
        return render_template('404.html'), 404

    user_timezone = pytz.timezone(teacher.timezone)
    
    if most_recent_record:
    # Ensure most_recent_record.lastEditTime and start_time are timezone-aware
        most_recent_record.lastEditTime = ensure_timezone_aware(most_recent_record.lastEditTime, teacher.timezone)
        most_recent_record.lesson_slot.start_time = ensure_timezone_aware(most_recent_record.lesson_slot.start_time, teacher.timezone)
    # Ensure start_time of each upcoming lesson is timezone-aware
    for lesson in upcoming_lessons:
        lesson.start_time = ensure_timezone_aware(lesson.start_time, teacher.timezone)
        
    for lesson in upcoming_lessons:
        print(lesson.start_time)

    # Pass the user_timezone to the template
    return render_template('teacher/teacher_dashboard.html', profile=current_user.profile, most_recent_record=most_recent_record, upcoming_lessons=upcoming_lessons, user_timezone=user_timezone)


@app.route('/teacher/lesson_records')
@login_required
def teacher_lesson_records():
    if session['user_type'] != 'teacher':
        return redirect(url_for('home'))

    # Fetch the teacher's timezone
    teacher = db.session.get(Teacher, session['user_id'])
    if teacher is None:
        app.logger.error(f"Teacher with ID {session['user_id']} not found.")
        return render_template('404.html'), 404

    page = request.args.get('page', 1, type=int)

    # Query past lesson records for the logged-in teacher
    lesson_records = LessonRecord.query.join(LessonSlot).filter(
        LessonRecord.teacher_id == session['user_id'],
        LessonSlot.start_time <= datetime.now(timezone.utc)
    ).options(
        joinedload(LessonRecord.student).joinedload(Student.profile)
    ).order_by(LessonSlot.start_time.desc()).paginate(page=page, per_page=5)

    for record in lesson_records.items:
        # Ensure record.lastEditTime is timezone-aware (helper function!)
        record.lastEditTime = ensure_timezone_aware(record.lastEditTime, teacher.timezone)
        # Ensure lesson slot start_time is timezone-aware
        if record.lesson_slot and record.lesson_slot.start_time:
            record.lesson_slot.start_time = ensure_timezone_aware(record.lesson_slot.start_time, teacher.timezone)

    return render_template('teacher/teacher_lesson_records.html', lesson_records=lesson_records)


@app.route('/teacher/edit_teacher_profile', methods=['GET', 'POST'])
@login_required
@limiter.limit("5/minute") 
def edit_teacher_profile():
    """
    Where teachers can edit and update their own profiles
    """
    
    if 'user_type' not in session or session['user_type'] != 'teacher':
        return redirect(url_for('login'))
    
    form = EditTeacherProfileForm(obj=current_user.profile)
    profile_updated = request.args.get('updated', False)

    if form.validate_on_submit():
        current_user.profile.age = form.age.data if form.age.data else None
        current_user.profile.hobbies = form.hobbies.data.strip() if form.hobbies.data else ''
        current_user.profile.motto = form.motto.data.strip() if form.motto.data else ''
        current_user.profile.blood_type = form.blood_type.data.strip() if form.blood_type.data else ''

        # Handle the image file separately because it's not a simple text field.
        if form.image_file.data:
            current_user.profile.image_file = save_image_file(form.image_file.data)

        db.session.commit()
        return redirect(url_for('edit_teacher_profile', updated=True))

    return render_template('teacher/edit_teacher_profile.html', form=form, profile=current_user.profile, profile_updated=profile_updated)

#    # Get the student's timezone
#    user_timezone = pytz.timezone(student.timezone)
#    week_offset = int(request.args.get('week_offset', 0))
 #   today = datetime.now(timezone.utc)
  #  today = datetime.now(timezone.utc).astimezone(user_timezone)
    
    # PERFECT WEEK OFFSET!
    # Calculate the start and end of the current week in the student/teacher's timezone
#    start_of_week = today - timedelta(days=today.weekday(), hours=today.hour, minutes=today.minute, seconds=today.second, microseconds=today.microsecond) + timedelta(weeks=week_offset)
 #   end_of_week = start_of_week + timedelta(days=6, hours=23, minutes=59)
  #  start_of_week_utc = start_of_week.astimezone(timezone.utc)
   # end_of_week_utc = end_of_week.astimezone(timezone.utc)
    #print(f"Book Lessons From {start_of_week.strftime('%A, %B %d, %Y %I:%M %p')} - {end_of_week.strftime('%A, %B %d, %Y %I:%M %p')}")


@app.route('/teacher/lesson_slots', methods=['GET', 'POST'])
@login_required
def manage_lesson_slots():
    form = LessonSlotsForm()
    teacher = db.session.get(Teacher, current_user.id)
    user_timezone = pytz.timezone(teacher.timezone)

    if request.method == 'POST':
        if form.validate_on_submit():
            try:
                response = manage_slot(request.form['start_time'], request.form['end_time'], current_user.id, user_timezone, 'open' if form.open.data else 'close')
                db.session.commit()
                return jsonify(response)
            except Exception as e:
                db.session.rollback()
                app.logger.error(f"Error creating or deleting lesson slot: {e}")
                return jsonify({'status': 'error', 'message': 'An error occurred while creating or deleting the lesson slot.'}), 500
        else:
            app.logger.error('Invalid form data.')
            return jsonify({'status': 'error', 'message': 'Invalid form data.'}), 400

    start_date_str = request.args.get('start_date')
    if start_date_str:
        try:
            start_date = datetime.strptime(start_date_str, '%Y-%m-%dT%H:%M:%S')
        except ValueError:
            start_date = datetime.strptime(start_date_str, '%Y-%m-%dT%H:%M')
        end_date = start_date + timedelta(days=6)
    else:
        today = datetime.now(user_timezone)
        start_date = today - timedelta(days=today.weekday())
        end_date = start_date + timedelta(days=6)
    
    start_date = start_date.replace(hour=7, minute=0, second=0, microsecond=0)
    end_date = end_date.replace(hour=23, minute=59, second=59, microsecond=999999)
    
    with db.session.no_autoflush:
        lesson_slots = LessonSlot.query.filter(
            LessonSlot.teacher_id == current_user.id,
            LessonSlot.start_time >= start_date.astimezone(pytz.UTC),
            LessonSlot.start_time <= end_date.astimezone(pytz.UTC)
        ).all()

    utc_now = datetime.now(pytz.UTC)
    lesson_slots_json = [{
        'slot_id': slot.id,
        'start_time': slot.start_time.astimezone(user_timezone).isoformat(),
        'end_time': slot.end_time.astimezone(user_timezone).isoformat(),
        'status': 'Booked' if slot.is_booked else 'Available' if slot.start_time.astimezone(pytz.UTC) > utc_now else 'Closed'
    } for slot in lesson_slots]

    # Log the data being sent
    app.logger.info(f"Returning lesson slots: {lesson_slots_json}")

    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        # Handle AJAX request
        return jsonify(lesson_slots_json)
    else:
        # Handle standard GET request
        return render_template('teacher/lesson_slots.html', form=form)


# Helper functions
def manage_slot(start_time_str, end_time_str, teacher_id, timezone, action):
    local_start_time = datetime.strptime(start_time_str, '%Y-%m-%dT%H:%M')
    start_time = timezone.localize(local_start_time).astimezone(pytz.UTC)
    local_end_time = datetime.strptime(end_time_str, '%Y-%m-%dT%H:%M')
    end_time = timezone.localize(local_end_time).astimezone(pytz.UTC)

    existing_slot = LessonSlot.query.filter_by(teacher_id=teacher_id, start_time=start_time, end_time=end_time).first()
    if existing_slot and action == 'close':
        db.session.delete(existing_slot)
        return {'status': 'success', 'message': 'Lesson slot closed!'}
    elif not existing_slot and action == 'open':
        new_slot = LessonSlot(teacher_id=teacher_id, start_time=start_time, end_time=end_time)
        db.session.add(new_slot)
        return {'status': 'success', 'message': 'New lesson slot created!'}
    else:
        return {'status': 'error', 'message': 'Invalid action or lesson slot does not exist.'}


    
def open_slot(start_time, end_time, teacher_id, timezone):
    start_time = ensure_timezone_aware(start_time, timezone)
    end_time = ensure_timezone_aware(end_time, timezone)
    new_slot = LessonSlot(teacher_id=teacher_id, start_time=start_time, end_time=end_time, is_booked=False)
    db.session.add(new_slot)
    db.session.commit()
    return {'status': 'success', 'slot_id': new_slot.id}

def close_slot(slot_id, teacher_id):
    slot = LessonSlot.query.get(slot_id)
    if slot and slot.teacher_id == teacher_id:
        db.session.delete(slot)
        db.session.commit()
        return {'status': 'success'}
    else:
        return {'status': 'error'}

@app.route('/teacher/update_slot', methods=['POST'])
@login_required
def update_lesson_slot():
    data = request.get_json()
    slot_id = data['slot_id']
    action = data['action']  # 'open' or 'close'

    teacher = db.session.get(Teacher, current_user.id)
    user_timezone = pytz.timezone(teacher.timezone)

    if action == 'open':
        local_start_time = datetime.strptime(data['start_time'], '%Y-%m-%dT%H:%M:%S')
        local_end_time = datetime.strptime(data['end_time'], '%Y-%m-%dT%H:%M:%S')
        return jsonify(open_slot(local_start_time, local_end_time, current_user.id, user_timezone))
    elif action == 'close':
        return jsonify(close_slot(slot_id, current_user.id))

    return jsonify({'status': 'error'})

@app.route('/update-slot-status', methods=['POST'])
@login_required
def update_slot_status():
    data = request.get_json()
    slot_id = data['slot_id']
    is_open = data['is_open']

    slot = LessonSlot.query.get(slot_id)
    if slot and slot.teacher_id == current_user.id:
        if slot.is_booked and is_open:
            return jsonify({'status': 'error', 'message': 'Cannot open a slot that is already booked.'})
        slot.is_booked = not is_open
        db.session.commit()
        return jsonify({'status': 'success'})

    return jsonify({'status': 'error'})

@app.route('/teacher/update_slots', methods=['POST'])
@login_required
def update_slots():
    data = request.get_json()
    app.logger.info(f"Received data: {data}")
    updates = []
    teacher = db.session.get(Teacher, current_user.id)

    for item in data:
        action = item['action']
        try:
            if action == 'open':
                local_start_time = datetime.fromisoformat(item['start_time'])
                start_time = ensure_timezone_aware(local_start_time, teacher.timezone)
                local_end_time = datetime.fromisoformat(item['end_time'])
                end_time = ensure_timezone_aware(local_end_time, teacher.timezone)
                new_slot = LessonSlot(teacher_id=current_user.id, start_time=start_time, end_time=end_time, is_booked=False)
                db.session.add(new_slot)
                db.session.commit()
                updates.append({
                    'action': 'open',
                    'slot_id': new_slot.id,
                    'start_time': new_slot.start_time.isoformat()
                })
            elif action == 'close':
                slot_id = item['slot_id']
                slot = LessonSlot.query.get(slot_id)
                if slot and slot.teacher_id == current_user.id:
                    if slot.is_booked:
                        return jsonify({'status': 'error', 'message': 'Cannot close a slot that is already booked.'})
                    db.session.delete(slot)
                    db.session.commit()
                    updates.append({
                        'action': 'close',
                        'slot_id': slot_id
                    })
                else:
                    app.logger.error('Invalid slot id.')
                    return render_template("apology.html", top="400 Error", bottom="Invalid slot id."), 400
        except Exception as e:
            app.logger.error(f"Error processing slot action: {e}")
            return render_template("apology.html", top="400 Error", bottom=f"Invalid data for {action} action."), 400

    return jsonify({'status': 'success', 'updates': updates})


@app.route('/student_profile/<int:student_id>', methods=['GET', 'POST'])
@login_required
@limiter.limit("5/minute") 
def student_profile(student_id):
    """
    This route lets a teacher view and edit a student's profile.
    Non-teachers are redirected to the home page.
    On a POST request, the student's profile is updated with form data and saved to the database,
    then the updated profile is displayed.
    On a GET request, the student's profile is passed to the 'view_student_profile.html'
    template for display.
    """
    # Ensure the current user is a teacher
    if session['user_type'] != 'teacher':
        return redirect(url_for('index'))

    # Fetch the student's profile
    student = db.session.get(Student, student_id)
    if student is None:
        app.logger.error(f"Student with ID {student_id} not found.")
        return render_template('404.html'), 404

    form = TeacherEditsStudentForm(obj=student.profile)
    profile_updated = request.args.get('updated', False)

    if form.validate_on_submit():
        student.profile.hometown = form.hometown.data.strip() if form.hometown.data else ''
        student.profile.goal = form.goal.data.strip() if form.goal.data else ''
        student.profile.hobbies = form.hobbies.data.strip() if form.hobbies.data else ''
        student.profile.correction_style = form.correction_style.data.strip() if form.correction_style.data else ''
        student.profile.english_weakness = form.english_weakness.data.strip() if form.english_weakness.data else ''

        db.session.commit()
        return redirect(url_for('student_profile', student_id=student.id, updated=True))

    # Pass the student's profile to the template
    return render_template('view_student_profile.html', form=form, student=student, profile_updated=profile_updated)


@app.route('/teacher/edit_lesson/<int:lesson_id>', methods=['GET', 'POST'])
@login_required
def edit_lesson(lesson_id):
    """
    Allow the teacher to edit a lesson record.
    """
    if session['user_type'] != 'teacher':
        return redirect(url_for('index'))

    lesson = db.session.get(LessonRecord, lesson_id)
    if lesson is None:
        app.logger.error(f"Lesson with ID {lesson_id} not found.")
        return render_template('404.html'), 404


    form = LessonRecordForm()  # Instantiate the updated form

    if form.validate_on_submit():
        lesson.lesson_summary = form.lesson_summary.data
        lesson.strengths = form.strengths.data
        lesson.areas_to_improve = form.areas_to_improve.data

        try:
            lesson.new_words = json.loads(form.new_words.data) if form.new_words.data else []
            lesson.new_phrases = json.loads(form.new_phrases.data) if form.new_phrases.data else []
        except json.JSONDecodeError:
            flash('Invalid input for new words or new phrases. Please try again.', 'danger')
            return render_template('teacher/edit_lesson.html', form=form, lesson=lesson)

        # Update the lesson edit time to the current UTC time
        lesson.lastEditTime = datetime.utcnow()

        db.session.commit()
        flash('Lesson updated successfully!', 'success')
        return redirect(url_for('teacher_dashboard'))

    # Pre-fill the form with existing data
    if request.method == 'GET':
        form.lesson_summary.data = lesson.lesson_summary
        form.strengths.data = lesson.strengths
        form.areas_to_improve.data = lesson.areas_to_improve
        form.new_words.data = json.dumps(lesson.new_words)
        form.new_phrases.data = json.dumps(lesson.new_phrases)

    # Converting To Teacher's Timezone
    teacher = db.session.get(Teacher, session['user_id'])
    today = datetime.now(timezone.utc)
    today = ensure_timezone_aware(today, teacher.timezone)
    
    # Convert the current time in the teacher's timezone to UTC
    utc_now = today.astimezone(pytz.utc)

    # Update the lesson edit time to the current UTC time
    lesson.lastEditTime = utc_now

    return render_template('teacher/edit_lesson.html', form=form, lesson=lesson)


# Student Only Routes!
@app.route('/student/dashboard')
@login_required
def student_dashboard():
    if session['user_type'] != 'student':
        return redirect(url_for('index'))

    # Fetch the student's timezone
    student = db.session.get(Student, session['user_id'])
    if student is None:
        app.logger.error(f"Student with ID {session['user_id']} not found.")
        return render_template('404.html'), 404
    
    try:
        user_timezone = pytz.timezone(student.timezone)
    except pytz.UnknownTimeZoneError:
        user_timezone = pytz.timezone('America/Los_Angeles')

    current_time = datetime.now(timezone.utc).astimezone(user_timezone)

    # Fetch the most recent past lesson record for the logged-in student
    most_recent_record = LessonRecord.query.filter(
        LessonRecord.student_id == session['user_id'],
        LessonRecord.lesson_slot.has(LessonSlot.start_time <= datetime.now(timezone.utc))
    ).options(
        joinedload(LessonRecord.teacher).joinedload(Teacher.profile),
        joinedload(LessonRecord.lesson_slot)
    ).order_by(LessonRecord.lastEditTime.desc()).first()

    # Fetch all upcoming lesson slots for the logged-in student
    upcoming_lessons = LessonSlot.query.join(Booking).filter(
        Booking.student_id == session['user_id'],
        LessonSlot.start_time >= datetime.now(timezone.utc)
    ).options(
        joinedload(LessonSlot.teacher).joinedload(Teacher.profile)
    ).order_by(LessonSlot.start_time.asc()).all()

    # Convert the lastEditTime of the most recent record to the user's timezone
    if most_recent_record:
        if most_recent_record.lastEditTime.tzinfo is None:
            most_recent_record.lastEditTime = pytz.utc.localize(most_recent_record.lastEditTime)
        most_recent_record.lastEditTime = most_recent_record.lastEditTime.astimezone(user_timezone)

        # Ensure lesson slot start_time is timezone-aware
        if most_recent_record.lesson_slot and most_recent_record.lesson_slot.start_time:
            if most_recent_record.lesson_slot.start_time.tzinfo is None:
                most_recent_record.lesson_slot.start_time = pytz.utc.localize(most_recent_record.lesson_slot.start_time).astimezone(user_timezone)
            else:
                most_recent_record.lesson_slot.start_time = most_recent_record.lesson_slot.start_time.astimezone(user_timezone)

    # Convert upcoming lesson times to the user's timezone
    for lesson in upcoming_lessons:
        if lesson.start_time.tzinfo is None:
            lesson.start_time = pytz.utc.localize(lesson.start_time)
        lesson.start_time = lesson.start_time.astimezone(user_timezone)

    cancel_lesson_form = CancelLessonForm()  # Define the cancel lesson form

    return render_template(
        'student/student_dashboard.html',
        profile=current_user.profile,
        most_recent_record=most_recent_record,
        upcoming_lessons=upcoming_lessons,
        cancel_lesson_form=cancel_lesson_form,  # Pass the cancel lesson form
        user_timezone=user_timezone  # Pass the timezone to the template
    )



@app.route('/cancel_lesson/<int:lesson_id>', methods=['POST'])
@login_required
def cancel_lesson(lesson_id):
    logging.debug("cancel_lesson route called")
    form = CancelLessonForm()
    logging.debug(f"Form data before validation: {request.form}")

    # Set lesson_id in the form's data
    form.lesson_id.data = lesson_id
    logging.debug(f"Lesson ID from URL: {lesson_id}")
    logging.debug(f"Lesson ID from form: {form.lesson_id.data}")

    if form.validate_on_submit():
        lesson_id = form.lesson_id.data
        logging.debug(f"Form validated. Lesson ID: {lesson_id}")

        # Fetch the booking from the database
        booking = Booking.query.filter_by(lesson_slot_id=lesson_id, student_id=current_user.id).first()
        if booking is None:
            logging.debug("Booking not found or invalid booking ID")
            flash('Invalid booking ID', 'error')
            return redirect(url_for('student_dashboard'))
        logging.debug(f"Booking found: {booking}")

        # Fetch the associated lesson slot
        lesson_slot = db.session.get(LessonSlot, lesson_id)
        if lesson_slot is None:
            logging.debug("Associated lesson slot not found")
            flash('Associated lesson slot not found', 'error')
            return redirect(url_for('student_dashboard'))
        logging.debug(f"Lesson slot found: {lesson_slot}")

        # Fetch the lesson record from the database
        lesson_record = LessonRecord.query.filter_by(id=booking.lesson_record_id).first()
        if lesson_record is not None:
            # Delete the lesson record entry
            db.session.delete(lesson_record)
            logging.debug("Lesson record deleted")
        else:
            logging.debug("Lesson record not found")

        # Delete the booking entry
        db.session.delete(booking)
        logging.debug("Booking deleted")

        # Update the lesson slot to set is_booked to False
        lesson_slot.is_booked = False
        logging.debug("Lesson slot updated")

        # Update the student's lesson counts
        student = db.session.get(Student, current_user.id)
        if student is not None:
            student.number_of_lessons -= 1
            logging.debug("Student lesson counts updated")
        else:
            logging.debug("Student not found")
            flash('Student not found', 'error')
            return redirect(url_for('student_dashboard'))

        # Commit the changes to the database
        try:
            db.session.commit()
            logging.debug("Changes committed to the database")
            flash('Lesson cancelled successfully', 'success')
        except Exception as e:
            db.session.rollback()
            logging.error(f"Error cancelling lesson: {e}")
            flash(f'Error cancelling lesson: {e}', 'error')

        return redirect(url_for('student_dashboard'))

    logging.debug(f"Form submission error: {form.errors}")
    flash('Form submission error. Please try again.', 'error')
    return redirect(url_for('student_dashboard'))


@app.route('/student/lesson_records')
@login_required
def student_lesson_records():
    if session.get('user_type') != 'student':
        return redirect(url_for('index'))
    
    # Fetch the student's timezone
    student = db.session.get(Student, session['user_id'])
    if student is None:
        app.logger.error(f"Student with ID {session['user_id']} not found.")
        return render_template('404.html'), 404
    
    try:
        user_timezone = pytz.timezone(student.timezone)
    except pytz.UnknownTimeZoneError:
        user_timezone = pytz.timezone('America/Los_Angeles')

    # Fetch all past lesson records for the logged-in student
    page = request.args.get('page', 1, type=int)
    lesson_records = LessonRecord.query.filter(
        LessonRecord.student_id == session['user_id'],
        LessonRecord.lesson_slot.has(LessonSlot.start_time <= datetime.now(timezone.utc))
    ).options(
        joinedload(LessonRecord.teacher).joinedload(Teacher.profile),
        joinedload(LessonRecord.lesson_slot)
    ).order_by(LessonRecord.lastEditTime.desc()).paginate(page=page, per_page=5)

    for record in lesson_records.items:
        # Ensure record.lastEditTime is timezone-aware
        record.lastEditTime = ensure_timezone_aware(record.lastEditTime, student.timezone)

        # Ensure lesson slot start_time is timezone-aware
        if record.lesson_slot and record.lesson_slot.start_time:
            record.lesson_slot.start_time = ensure_timezone_aware(record.lesson_slot.start_time, student.timezone)
            
    return render_template('student/lesson_records.html', lesson_records=lesson_records, user_timezone=user_timezone)


@app.route('/student/edit_student_profile', methods=['GET', 'POST'])
@login_required
@limiter.limit("5/minute") 
def edit_student_profile():
    if 'user_type' not in session or session['user_type'] != 'student':
        return redirect(url_for('login'))
    
    if current_user.profile is None:
        profile = StudentProfile(student_id=current_user.id, image_file='default1.png')
        db.session.add(profile)
        db.session.commit()
        current_user.profile = profile
    
    form = StudentProfileForm(obj=current_user.profile)
    if form.validate_on_submit():
        current_user.profile.hometown = form.hometown.data.strip() if form.hometown.data else ''
        current_user.profile.goal = form.goal.data.strip() if form.goal.data else ''
        current_user.profile.hobbies = form.hobbies.data.strip() if form.hobbies.data else ''
        current_user.profile.correction_style = form.correction_style.data.strip() if form.correction_style.data else ''
        current_user.profile.english_weakness = form.english_weakness.data.strip() if form.english_weakness.data else ''

        if form.image_file.data:
            current_user.profile.image_file = save_image_file(form.image_file.data)

        db.session.commit()
        return redirect(url_for('edit_student_profile', updated=True))

    return render_template('student/edit_student_profile.html', form=form, profile=current_user.profile, profile_updated=request.args.get('updated', False))


@app.route('/student/book_lesson', methods=['GET', 'POST'])
@login_required
def student_book_lesson():
    """
    This allows a student to book a lesson with a teacher.
    They search for an open lesson_slot, and then book it.
    Forms are used for CSRF! (Care taken with XSS)
    """
    form = StudentLessonSlotForm()
    
    student = db.session.get(Student, current_user.id)
    if student is None:
        app.logger.error(f"Student with ID {current_user.id} not found.")
        return render_template('404.html'), 404
    
    # Get the student's timezone
    user_timezone = pytz.timezone(student.timezone)
    week_offset = int(request.args.get('week_offset', 0))
    today = datetime.now(timezone.utc)
    today = datetime.now(timezone.utc).astimezone(user_timezone)
    
    # PERFECT WEEK OFFSET!
    # Calculate the start and end of the current week in the student/teacher's timezone
    start_of_week = today - timedelta(days=today.weekday(), hours=today.hour, minutes=today.minute, seconds=today.second, microseconds=today.microsecond) + timedelta(weeks=week_offset)
    end_of_week = start_of_week + timedelta(days=6, hours=23, minutes=59)
    start_of_week_utc = start_of_week.astimezone(timezone.utc)
    end_of_week_utc = end_of_week.astimezone(timezone.utc)
    print(f"Book Lessons From {start_of_week.strftime('%A, %B %d, %Y %I:%M %p')} - {end_of_week.strftime('%A, %B %d, %Y %I:%M %p')}")

    if request.method == 'POST':
        # Retrieve available slots from session
        available_slots_dict = session.get('available_slots', None)
        if available_slots_dict is None:
            return redirect(url_for('login'))

        available_slots = [
            type('LessonSlot', (object,), {
                'id': slot_dict['id'],
                'start_time': datetime.fromisoformat(slot_dict['start_time']),
                'end_time': datetime.fromisoformat(slot_dict['end_time']),
                'teacher': type('Teacher', (object,), {
                    'id': slot_dict['teacher_id'],
                    'username': slot_dict['teacher_username']
                })()
            })()
            for slot_dict in available_slots_dict
        ]
    else:
        # Fetch available lesson slots within the specified week and in the future
        teacher_id_str = request.args.get('teacher_id')
        teacher_id = int(teacher_id_str) if teacher_id_str is not None else None
        available_slots = LessonSlot.query.filter(
            LessonSlot.start_time.between(start_of_week_utc, end_of_week_utc),
            LessonSlot.start_time > datetime.now(timezone.utc),
            LessonSlot.is_booked == False,
            (LessonSlot.teacher_id == teacher_id) if teacher_id is not None else True,
        ).order_by(LessonSlot.start_time.asc()).all()

        # Convert each LessonSlot object to a dictionary
        available_slots_dict = [
            {
                'id': slot.id,
                'start_time': slot.start_time.isoformat(),
                'end_time': slot.end_time.isoformat(),
                'teacher_id': slot.teacher.id,
                'teacher_username': slot.teacher.username,
            }
            for slot in available_slots
        ]
        # Store the list of dictionaries in the session for use later
        session['available_slots'] = available_slots_dict

    # Convert lesson times to the student's timezone
    for slot in available_slots:
        slot.start_time = ensure_timezone_aware(slot.start_time, student.timezone)
        slot.end_time = ensure_timezone_aware(slot.end_time, student.timezone)
        
    # Get the current time in the student's timezone
    current_time = datetime.now(user_timezone)
    
    form.lesson_slot.choices = [
        (slot.id, f"{slot.start_time.strftime('%Y-%m-%d %I:%M %p')} - {slot.end_time.strftime('%I:%M %p')} with {slot.teacher.username}")
        for slot in available_slots
    ]

    # Filter available teachers based on available slots
    available_teacher_ids = {slot.teacher.id for slot in available_slots}
    available_teachers = [teacher for teacher in Teacher.query.all() if teacher.id in available_teacher_ids]
    form.teacher.choices = [(teacher.id, teacher.username) for teacher in available_teachers]

    if request.method == 'POST' and form.validate_on_submit():
        lesson_slot_id = form.lesson_slot.data
        teacher_id = form.teacher.data

        if not lesson_slot_id or not teacher_id:
            print('Please select a valid lesson slot and teacher.')
            return render_template(
                'student/book_lesson.html', 
                form=form, 
                available_slots=available_slots, 
                available_teachers=available_teachers,
                week_offset=week_offset, 
                remaining_lessons=student.remaining_lessons, 
                start_of_week=start_of_week, 
                end_of_week=end_of_week)

        lesson_slot = db.session.get(LessonSlot, lesson_slot_id)
        if lesson_slot is None:
            print('Invalid lesson slot selected')
            return render_template(
                'student/book_lesson.html', 
                form=form, 
                available_slots=available_slots, 
                available_teachers=available_teachers, 
                week_offset=week_offset, 
                remaining_lessons=student.remaining_lessons, 
                start_of_week=start_of_week, 
                end_of_week=end_of_week)

        if lesson_slot.is_booked or ensure_timezone_aware(lesson_slot.start_time, student.timezone) < current_time:
            print('Lesson slot is not available')
            return render_template(
                'student/book_lesson.html', 
                form=form, 
                available_slots=available_slots, 
                available_teachers=available_teachers, 
                week_offset=week_offset, 
                remaining_lessons=student.remaining_lessons, 
                start_of_week=start_of_week, 
                end_of_week=end_of_week)

        if student.lessons_purchased <= student.number_of_lessons:
            print('Not enough points to book a lesson')
            return render_template(
                'student/book_lesson.html', 
                form=form, 
                available_slots=available_slots, 
                available_teachers=available_teachers, 
                week_offset=week_offset, 
                remaining_lessons=student.remaining_lessons, 
                start_of_week=start_of_week, 
                end_of_week=end_of_week)

        lesson_record = LessonRecord(student_id=current_user.id, teacher_id=teacher_id, lesson_slot_id=lesson_slot.id)
        db.session.add(lesson_record)
        db.session.flush()

        booking = Booking(student_id=student.id, lesson_slot_id=lesson_slot.id, status='booked', lesson_record_id=lesson_record.id)
        db.session.add(booking)

        lesson_slot.is_booked = True
        student.number_of_lessons += 1

        session['available_slots'] = [slot for slot in session['available_slots'] if slot['id'] != lesson_slot_id]

        try:
            db.session.commit()
            print('Lesson booked successfully')
            return redirect(url_for('student_book_lesson', week_offset=week_offset))
        except Exception as e:
            db.session.rollback()
            print(f'Error booking lesson: {e}')
            return render_template(
                'student/book_lesson.html', 
                form=form, 
                available_slots=available_slots, 
                available_teachers=available_teachers, 
                week_offset=week_offset, 
                remaining_lessons=student.remaining_lessons, 
                start_of_week=start_of_week, 
                end_of_week=end_of_week)

    elif request.method == 'POST':
        print('Form validation failed')
        print(form.errors)

    return render_template(
        'student/book_lesson.html', 
        form=form, 
        available_slots=available_slots, 
        available_teachers=available_teachers, 
        week_offset=week_offset, 
        remaining_lessons=student.remaining_lessons, 
        start_of_week=start_of_week, 
        end_of_week=end_of_week)


# Flask route
@app.route('/get_slots/<int:teacher_id>', methods=['GET'])
def get_slots(teacher_id):
    # Check if the student is logged in
    if 'user_id' not in session:
        return jsonify({'error': 'Not logged in'}), 401

    # Get the student's timezone
    student = db.session.get(Student, session['user_id'])

    if student is None:
        return jsonify({'error': 'Student not found'}), 404

    # Get the start and end of the week in the student's timezone
    start_of_week, end_of_week = get_week_boundaries(student.timezone)
    
    user_timezone = pytz.timezone(student.timezone)
    # Get the current time in the user's timezone
    current_time = datetime.now(user_timezone)
    current_time_utc = current_time.astimezone(pytz.UTC)

    # Fetch the slots for the teacher that are within the current week and in the future
    slots = LessonSlot.query.filter(
        LessonSlot.teacher_id == teacher_id,
        LessonSlot.is_booked == False,
        LessonSlot.start_time >= start_of_week,
        LessonSlot.start_time <= end_of_week,
        LessonSlot.start_time >= current_time_utc  # Add this line
    ).all()

    slots_dict = [{'id': slot.id, 'time': slot.start_time.replace(tzinfo=timezone.utc).astimezone(user_timezone).strftime('%Y-%m-%d %I:%M %p'), 'teacher': slot.teacher.username} for slot in slots]
    return jsonify(slots_dict)


@app.teardown_appcontext
def shutdown_session(exception=None):
    db.session.remove()

if __name__ == '__main__':
    app.run(debug=True)