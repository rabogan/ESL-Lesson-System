import json
import pytz
from helpers import save_image_file
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
from wtforms import StringField, PasswordField, SubmitField, BooleanField, HiddenField, IntegerField, FileField, TextAreaField, HiddenField
from wtforms.validators import DataRequired, Length, Email, EqualTo, Optional, NumberRange

# Initialize Flask app
app = Flask(__name__)
app.secret_key = 'coolie_killer_huimin_himitsunakotogawaruidesune'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///site.db'
app.config['DEBUG'] = True

# Initialize extensions
db = SQLAlchemy(app)
migrate = Migrate(app, db)
login_manager = LoginManager()
login_manager.init_app(app)
csrf = CSRFProtect(app)
csrf.init_app(app)

#GUESS
class LessonSlotsForm(FlaskForm):
    csrf_token = HiddenField()

class RegistrationForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(min=2, max=20)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    confirmation = PasswordField('Confirm Password', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Register')


class LoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(min=2, max=20)])
    password = PasswordField('Password', validators=[DataRequired()])
    remember = BooleanField('Remember Me')
    submit = SubmitField('Login')


class EditTeacherProfileForm(FlaskForm):
    age = IntegerField('Age', validators=[Optional(), NumberRange(min=0)])
    hobbies = StringField('Hobbies', validators=[Optional(), Length(max=500)])
    motto = StringField('Motto', validators=[Optional(), Length(max=500)])
    blood_type = StringField('Blood Type', validators=[Optional(), Length(max=5)])
    image_file = FileField('Profile Image', validators=[Optional(), FileAllowed(['jpg', 'png'])])
    submit = SubmitField('Update Profile')
    
    
class StudentProfileForm(FlaskForm):
    hometown = StringField('Hometown', validators=[Optional(), Length(max=500)])
    goal = StringField('Goal', validators=[Optional(), Length(max=1000)])
    hobbies = StringField('Hobbies', validators=[Optional(), Length(max=1000)])
    correction_style = StringField('Correction Style', validators=[Optional(), Length(max=1000)])
    english_weakness = StringField('English Weakness', validators=[Optional(), Length(max=1000)])
    image_file = FileField('Profile Image', validators=[Optional(), FileAllowed(['jpg', 'png'])])
    submit = SubmitField('Update Profile')
    

class TeacherEditsStudentForm(FlaskForm):
    hometown = StringField('Hometown', validators=[Optional(), Length(max=500)])
    goal = StringField('Goal', validators=[Optional(), Length(max=1000)])
    hobbies = StringField('Hobbies', validators=[Optional(), Length(max=1000)])
    correction_style = StringField('Correction Style', validators=[Optional(), Length(max=1000)])
    english_weakness = StringField('English Weakness', validators=[Optional(), Length(max=1000)])
    submit = SubmitField('Update Profile')

class LessonRecordForm(FlaskForm):
    lesson_summary = TextAreaField('Lesson Summary', validators=[DataRequired()])
    strengths = TextAreaField('Strengths', validators=[DataRequired()])
    areas_to_improve = TextAreaField('Areas to Improve', validators=[DataRequired()])
    new_words = HiddenField('New Words')
    new_phrases = HiddenField('New Phrases')
    submit = SubmitField('Update Lesson')

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
    lessons_purchased = db.Column(db.Integer, default=1)
    timezone = db.Column(db.String(50), default='America/Los_Angeles')
    profile = db.relationship('StudentProfile', uselist=False, back_populates='student')
    lesson_records = db.relationship('LessonRecord', back_populates='student')
    bookings = db.relationship('Booking', back_populates='student')

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
    date = db.Column(db.DateTime, default=datetime.utcnow)

    student = db.relationship('Student', back_populates='lesson_records')
    teacher = db.relationship('Teacher', back_populates='lesson_records')
    lesson_slot = db.relationship('LessonSlot', back_populates='lesson_records')

    def __repr__(self):
        return f"LessonRecord('{self.strengths}', '{self.areas_to_improve}', '{self.lesson_summary}')"



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
    status = db.Column(db.String(20), nullable=False, default='booked')
    student = db.relationship('Student', back_populates='bookings')
    lesson_slot = db.relationship('LessonSlot', back_populates='booking')

    def __repr__(self):
        return f"Booking('{self.student_id}', '{self.lesson_slot_id}', '{self.status}')"


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


@app.route('/portal_choice')
def portal_choice():
    """
    This is where the user chooses whether to log in/register as a student or teacher.
    """
    return render_template('portal_choice.html')


@app.route("/student/register", methods=["GET", "POST"])
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
def teacher_register():
    """
    Allow new teachers to register for the platform
    """
    form = RegistrationForm()
    if form.validate_on_submit():
        username = form.username.data
        email = form.email.data
        password = form.password.data
        confirmation = form.confirmation.data

        # Input valdidity check
        if not username:
            return render_template("apology.html", top="Error", bottom="Please provide a valid username"), 400
        if not password:
            return render_template("apology.html", top="Error", bottom="Please provide a password"), 400
        if not confirmation:
            return render_template("apology.html", top="Error", bottom="Confirmation not provided"), 400
        if password != confirmation:
            return render_template("apology.html", top="Error", bottom="Password and confirmation must match!"), 400

        # Check if the username already exists
        existing_teacher = Teacher.query.filter_by(username=username).first()
        if existing_teacher is not None:
            return render_template("apology.html", top="Error", bottom="Username already exists"), 400

        hashed_password = generate_password_hash(password)
        new_teacher = Teacher(username=username, email=email, password=hashed_password)
        db.session.add(new_teacher)
        db.session.commit()

        # Create a new TeacherProfile for the newly registered teacher
        profile = TeacherProfile(teacher_id=new_teacher.id, image_file='default.jpg')
        db.session.add(profile)
        db.session.commit()

        # Store the user_id, user_type and user_name in the session
        session['user_id'] = new_teacher.id
        session['user_type'] = 'teacher'
        session['user_name'] = new_teacher.username

        return redirect(url_for("teacher_login"))
    return render_template("teacher_register.html", form=form)


@app.route("/teacher/login", methods=["GET", "POST"])
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
        session['user_type'] = 'teacher'
        session['user_name'] = teacher.username

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
            LessonRecord.date <= datetime.now(timezone.utc),
            LessonRecord.lesson_summary.isnot(None)
        )
    ).options(
        joinedload(LessonRecord.student).joinedload(Student.profile)
    ).order_by(LessonRecord.date.desc()).first()

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
        return abort(404)

    user_timezone = pytz.timezone(teacher.timezone)
    if most_recent_record:
        most_recent_record.date = most_recent_record.date.astimezone(user_timezone)
    for lesson in upcoming_lessons:
        lesson.start_time = lesson.start_time.astimezone(user_timezone)

    return render_template('teacher/teacher_dashboard.html', profile=current_user.profile, most_recent_record=most_recent_record, upcoming_lessons=upcoming_lessons)


@app.route('/teacher/lesson_records')
@login_required
def teacher_lesson_records():
    if session['user_type'] != 'teacher':
        return redirect(url_for('home'))

    # Fetch the teacher's timezone
    teacher = db.session.get(Teacher, session['user_id'])
    user_timezone = pytz.timezone(teacher.timezone)

    page = request.args.get('page', 1, type=int)

    # Query all lesson records for the logged-in teacher, join with LessonSlot, and order by LessonSlot.start_time
    lesson_records = LessonRecord.query.join(LessonSlot).filter(
        LessonRecord.teacher_id == session['user_id']
    ).options(
        joinedload(LessonRecord.student).joinedload(Student.profile)
    ).order_by(LessonSlot.start_time.desc()).paginate(page=page, per_page=5)

    for record in lesson_records.items:
        # Ensure record.date is timezone-aware
        if record.date.tzinfo is None:
            record.date = pytz.utc.localize(record.date).astimezone(user_timezone)
        else:
            record.date = record.date.astimezone(user_timezone)

    return render_template('teacher/teacher_lesson_records.html', lesson_records=lesson_records)



@app.route('/teacher/edit_teacher_profile', methods=['GET', 'POST'])
@login_required
def edit_teacher_profile():
    """
    Where teachers can edit and update their own profiles
    """
    form = EditTeacherProfileForm(obj=current_user.profile)

    if form.validate_on_submit():
        current_user.profile.age = form.age.data
        current_user.profile.hobbies = form.hobbies.data
        current_user.profile.motto = form.motto.data
        current_user.profile.blood_type = form.blood_type.data

        # Handle the image file separately because it's not a simple text field.
        if form.image_file.data:
            current_user.profile.image_file = save_image_file(form.image_file.data)

        db.session.commit()
        flash('Your profile has been updated!', 'success')
        return redirect(url_for('teacher_dashboard'))

    return render_template('teacher/edit_teacher_profile.html', form=form, profile=current_user.profile)


@app.route('/teacher/lesson_slots', methods=['GET', 'POST'])
@login_required
def manage_lesson_slots():
    form = LessonSlotsForm()
    teacher = db.session.get(Teacher, current_user.id)
    user_timezone = pytz.timezone(teacher.timezone)

    if request.method == 'POST' and form.validate_on_submit():
        try:
            local_start_time = datetime.strptime(request.form['start_time'], '%Y-%m-%dT%H:%M')
            start_time = user_timezone.localize(local_start_time).astimezone(pytz.UTC)
            local_end_time = datetime.strptime(request.form['end_time'], '%Y-%m-%dT%H:%M')
            end_time = user_timezone.localize(local_end_time).astimezone(pytz.UTC)
            new_slot = LessonSlot(teacher_id=current_user.id, start_time=start_time, end_time=end_time)
            db.session.add(new_slot)
            db.session.commit()
            flash('New lesson slot created!', 'success')
        except Exception as e:
            db.session.rollback()
            app.logger.error(f"Error creating lesson slot: {e}")
            flash('An error occurred while creating the lesson slot.', 'danger')

    start_date_str = request.args.get('start_date')
    if start_date_str:
        start_date = user_timezone.localize(datetime.strptime(start_date_str, '%Y-%m-%d'))
    else:
        start_date = datetime.now(user_timezone) - timedelta(days=datetime.now(user_timezone).weekday())

    end_date = start_date + timedelta(days=6)
    with db.session.no_autoflush:
        lesson_slots = LessonSlot.query.filter(
            LessonSlot.teacher_id == current_user.id,
            LessonSlot.start_time >= start_date.astimezone(pytz.UTC),
            LessonSlot.start_time <= end_date.astimezone(pytz.UTC)
        ).all()

        for slot in lesson_slots:
            slot.start_time = slot.start_time.astimezone(user_timezone)
            slot.end_time = slot.end_time.astimezone(user_timezone)

    return render_template('teacher/lesson_slots.html',
                           lesson_slots=lesson_slots,
                           start_date=start_date,
                           end_date=end_date,
                           datetime=datetime,
                           timedelta=timedelta,
                           pytz=pytz,
                           user_timezone=user_timezone,
                           form=form)



@app.route('/teacher/update_slot', methods=['POST'])
@login_required
def update_lesson_slot():
    data = request.get_json()
    slot_id = data['slot_id']
    action = data['action']  # 'open' or 'close'
    
    teacher = db.session.get(Teacher, current_user.id)
    user_timezone = pytz.timezone(teacher.timezone)

    if action == 'open':
        local_start_time = datetime.strptime(data['start_time'], '%Y-%m-%d %H:%M:%S')
        start_time = user_timezone.localize(local_start_time).astimezone(pytz.UTC)
        local_end_time = datetime.strptime(data['end_time'], '%Y-%m-%d %H:%M:%S')
        end_time = user_timezone.localize(local_end_time).astimezone(pytz.UTC)
        new_slot = LessonSlot(teacher_id=current_user.id, start_time=start_time, end_time=end_time, is_booked=False)
        db.session.add(new_slot)
        db.session.commit()
        return jsonify({'status': 'success', 'slot_id': new_slot.id})
    elif action == 'close':
        slot = LessonSlot.query.get(slot_id)
        if slot and slot.teacher_id == current_user.id:
            db.session.delete(slot)
            db.session.commit()
            return jsonify({'status': 'success'})

    return jsonify({'status': 'error'})


@app.route('/teacher/update_slots', methods=['POST'])
@login_required
def update_slots():
    data = request.get_json()
    teacher = db.session.get(Teacher, current_user.id)
    user_timezone = pytz.timezone(teacher.timezone)
    
    for item in data:
        action = item['action']
        start_time = item['start_time']
        end_time = item['end_time']

        if action == 'open':
            try:
                # Parse the datetimes
                start_time = datetime.fromisoformat(start_time).replace(tzinfo=None)
                end_time = datetime.fromisoformat(end_time).replace(tzinfo=None)
                
                # Localize them to the user's timezone
                start_time = user_timezone.localize(start_time)
                end_time = user_timezone.localize(end_time)
                
                # Create the new lesson slot
                new_slot = LessonSlot(
                    teacher_id=current_user.id,
                    start_time=start_time,
                    end_time=end_time,
                    is_booked=False
                )
                db.session.add(new_slot)
                db.session.commit()
                app.logger.info(f"Opened slot: {new_slot.id} from {new_slot.start_time} to {new_slot.end_time}")
            except Exception as e:
                app.logger.error(f"Error processing open action: {e}")
                return jsonify({'status': 'error', 'message': 'Invalid data for open action'}), 400

        elif action == 'close':
            slot_id = item['slot_id']
            slot = db.session.get(LessonSlot, slot_id)
            if slot and slot.teacher_id == current_user.id:
                db.session.delete(slot)
                db.session.commit()
                app.logger.info(f"Closed slot: {slot_id}")
            else:
                app.logger.error(f"Slot {slot_id} not found or unauthorized")
                return jsonify({'status': 'error', 'message': 'Invalid slot ID or unauthorized'}), 400

    return jsonify({'status': 'success'})



@app.route('/student_profile/<int:student_id>', methods=['GET', 'POST'])
@login_required
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
        return redirect(url_for('home'))

    # Fetch the student's profile
    student = db.session.get(Student, student_id)
    if student is None:
        app.logger.error(f"Student with ID {student_id} not found.")
        return abort(404)

    form = TeacherEditsStudentForm(obj=student.profile)

    if form.validate_on_submit():
        student.profile.hometown = form.hometown.data
        student.profile.goal = form.goal.data
        student.profile.hobbies = form.hobbies.data
        student.profile.correction_style = form.correction_style.data
        student.profile.english_weakness = form.english_weakness.data

        db.session.commit()
        flash('Student profile has been updated!', 'success')
        return redirect(url_for('student_profile', student_id=student.id))

    # Pass the student's profile to the template
    return render_template('view_student_profile.html', form=form, student=student)



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
        return abort(404)

    form = LessonRecordForm()

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

        # Update the lesson date to the current UTC time
        lesson.date = datetime.utcnow()

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

    # Fetch the teacher's timezone
    teacher = db.session.get(Teacher, session['user_id'])
    user_timezone = pytz.timezone(teacher.timezone)

    # Convert lesson date to teacher's timezone
    lesson.date = lesson.date.astimezone(user_timezone)

    return render_template('teacher/edit_lesson.html', form=form, lesson=lesson)


# Student Only Routes@app.route('/student/dashboard')
@login_required
def student_dashboard():
    if session['user_type'] != 'student':
        return redirect(url_for('index'))

    # Fetch the most recent lesson record for the logged-in student
    most_recent_record = LessonRecord.query.filter_by(student_id=session['user_id']).options(
        joinedload(LessonRecord.teacher).joinedload(Teacher.profile)
    ).order_by(LessonRecord.date.desc()).first()

    # Fetch all upcoming lesson slots for the logged-in student
    upcoming_lessons = LessonSlot.query.join(Booking).filter(
        Booking.student_id == session['user_id'],
        LessonSlot.start_time >= datetime.now(timezone.utc)
    ).options(
        joinedload(LessonSlot.teacher).joinedload(Teacher.profile)
    ).order_by(LessonSlot.start_time.asc()).all()

    # Convert lesson times to the user's timezone
    student = db.session.get(Student, session['user_id'])
    if student is None:
        return abort(404)

    user_timezone = pytz.timezone(student.timezone) if student.timezone else pytz.timezone('America/Los_Angeles')
    try:
        user_timezone = pytz.timezone(student.timezone)
    except pytz.UnknownTimeZoneError:
        user_timezone = pytz.timezone('America/Los_Angeles')

    for lesson in upcoming_lessons:
        lesson.start_time = lesson.start_time.astimezone(user_timezone)

    # Pass the most recent record, the upcoming lessons, and the profile to the template
    return render_template(
        'student/student_dashboard.html',
        profile=current_user.profile,
        most_recent_record=most_recent_record,
        upcoming_lessons=upcoming_lessons
    )


class CancelLessonForm(FlaskForm):
    lesson_id = HiddenField('Lesson ID', validators=[DataRequired()])


@app.route('/cancel_lesson', methods=['POST'])
@login_required
def cancel_lesson():
    if session['user_type'] != 'student':
        return redirect(url_for('home'))

    form = CancelLessonForm()
    
    if form.validate_on_submit():
        lesson_id = form.lesson_id.data

        # Fetch the lesson record from the database
        lesson = db.session.get(LessonRecord, lesson_id)
        if lesson is None or lesson.student_id != session['user_id']:
            # If not, redirect the user back to the dashboard with an error message
            flash('Invalid lesson ID', 'error')
            return redirect(url_for('student_dashboard'))

        # Delete the lesson record from the database
        db.session.delete(lesson)
        db.session.commit()

        # Redirect the user back to the dashboard with a success message
        flash('Lesson cancelled successfully', 'success')
        return redirect(url_for('student_dashboard'))
    
    flash('Form submission error. Please try again.', 'error')
    return redirect(url_for('student_dashboard'))



@app.route('/student/lesson_records')
@login_required
def student_lesson_records():
    if session.get('user_type') != 'student':
        return redirect(url_for('index'))
    # Fetch all lesson records for the logged-in student
    page = request.args.get('page', 1, type=int)
    lesson_records = LessonRecord.query.filter_by(student_id=session['user_id']).options(
        joinedload(LessonRecord.teacher).joinedload(Teacher.profile)
    ).order_by(LessonRecord.date.desc()).paginate(page=page, per_page=5)

    return render_template('student/lesson_records.html', lesson_records=lesson_records)


@app.route('/student/edit_student_profile', methods=['GET', 'POST'])
@login_required
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
        current_user.profile.hometown = form.hometown.data
        current_user.profile.goal = form.goal.data
        current_user.profile.hobbies = form.hobbies.data
        current_user.profile.correction_style = form.correction_style.data
        current_user.profile.english_weakness = form.english_weakness.data

        if form.image_file.data:
            current_user.profile.image_file = save_image_file(form.image_file.data)

        db.session.commit()
        flash('Your profile has been updated!', 'success')
        return redirect(url_for('student_dashboard'))

    return render_template('student/edit_student_profile.html', form=form, profile=current_user.profile)


@app.route('/student/book_lesson', methods=['GET', 'POST'])
@login_required
def student_book_lesson():
    if request.method == 'POST':
        lesson_slot_id = request.form.get('lesson_slot')
        teacher_id = request.form.get('teacher')

        # Fetch the lesson slot
        lesson_slot = db.session.get(LessonSlot, lesson_slot_id)
        if lesson_slot is None:
            return abort(404)

        # Get the current student's timezone
        student = db.session.get(Student, current_user.id)
        if student is None:
            return abort(404)

        user_timezone = pytz.timezone(student.timezone)

        # Convert lesson_slot.start_time to the student's timezone for comparison
        lesson_start_time = lesson_slot.start_time.astimezone(user_timezone)

        # Get the current time in the student's timezone
        current_time = datetime.now(user_timezone)

        # Check if the lesson slot exists and is not already booked
        if lesson_slot.is_booked or lesson_start_time < current_time:
            flash('Lesson slot is not available', 'error')
            return redirect(url_for('student_dashboard'))

        # Check if the student has enough lessons purchased
        if student.lessons_purchased <= student.number_of_lessons:
            flash('Not enough lessons purchased', 'error')
            return redirect(url_for('student_dashboard'))
        
        # Create a new booking
        booking = Booking(student_id=student.id, lesson_slot_id=lesson_slot.id, status='booked')
        db.session.add(booking)

        # Update the lesson slot and student
        lesson_slot.is_booked = True
        student.number_of_lessons += 1

        # Create a new lesson record
        lesson_record = LessonRecord(
            student_id=current_user.id,
            teacher_id=teacher_id,
            lesson_slot_id=lesson_slot.id,
            date=lesson_slot.start_time
        )
        db.session.add(lesson_record)

        # Commit the changes to the database
        db.session.commit()

        flash('Lesson booked successfully', 'success')
        return redirect(url_for('student_dashboard'))
    else:  # GET request
        week_offset = int(request.args.get('week_offset', 0))
        start_of_week = datetime.now(timezone.utc) + timedelta(weeks=week_offset)
        end_of_week = start_of_week + timedelta(days=7)

        # Fetch available lesson slots within the specified week
        available_slots = LessonSlot.query.filter(
            LessonSlot.start_time.between(start_of_week, end_of_week),
            LessonSlot.is_booked == False
        ).options(
            joinedload(LessonSlot.teacher).joinedload(Teacher.profile)
        ).order_by(LessonSlot.start_time.asc()).all()

        # Fetch teachers who have available slots
        available_teachers = {slot.teacher for slot in available_slots}

        # Convert lesson times to the student's timezone
        student = db.session.get(Student, current_user.id)
        if student is None:
            return abort(404)

        user_timezone = pytz.timezone(student.timezone)
        for slot in available_slots:
            slot.start_time = slot.start_time.astimezone(user_timezone)
            slot.end_time = slot.end_time.astimezone(user_timezone)

        return render_template(
            'student/book_lesson.html',
            available_slots=available_slots,
            available_teachers=available_teachers,
            week_offset=week_offset
        )


@app.teardown_appcontext
def shutdown_session(exception=None):
    db.session.remove()

if __name__ == '__main__':
    app.run(debug=True)