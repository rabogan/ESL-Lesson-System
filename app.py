import json
from helpers import save_image_file
from flask import Flask, session, render_template, request, redirect, url_for, flash, jsonify
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import types, and_
from sqlalchemy.orm import joinedload
from flask_migrate import Migrate
from datetime import datetime, timedelta
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = 'coolie_killer_huimin_himitsunakotogawaruidesune'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///site.db'
app.config['DEBUG'] = True
db = SQLAlchemy(app)
migrate = Migrate(app, db)

# Flask-Login initialization
login_manager = LoginManager()
login_manager.init_app(app)

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
    db.create_all()
    print("Tables created")
        

# This handles whether a student or teacher is logging in
@login_manager.user_loader
def load_user(user_id):
    user_type = session.get('user_type')
    if user_type == 'student':
        return Student.query.get(int(user_id))
    elif user_type == 'teacher':
        return Teacher.query.get(int(user_id))
    else:
        return None
    

# Temporary Routes for Testing
@app.route("/test_students", methods=["GET"])
def get_students():
    page = request.args.get('page', 1, type=int)
    students = Student.query.paginate(page=page, per_page=5)
    return render_template("test/students.html", students=students)


@app.route("/test_teachers", methods=["GET"])
def get_teachers():
    page = request.args.get('page', 1, type=int)
    teachers = Teacher.query.paginate(page=page, per_page=5)
    return render_template("test/teachers.html", teachers=teachers)


@app.route("/test_lessons", methods=["GET"])
def get_lessons():
    page = request.args.get('page', 1, type=int)
    lessons = LessonRecord.query.paginate(page=page, per_page=5)
    return render_template("test/lessons.html", lessons=lessons)


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
    if request.method == "POST":
        username = request.form.get("username")
        email = request.form.get("email")
        password = request.form.get("password")
        confirmation = request.form.get("confirmation")

        # Check input validity
        if not username:
            return render_template("apology.html", top="Error", bottom="Please provide a valid username"), 400
        if not password:
            return render_template("apology.html", top="Error", bottom="Please provide a password"), 400
        if not confirmation:
            return render_template("apology.html", top="Error", bottom="Confirmation not provided"), 400
        if password != confirmation:
            return render_template("apology.html", top="Error", bottom="Password and confirmation must match!"), 400

        # Check if the username already exists
        existing_student = Student.query.filter_by(username=username).first()
        if existing_student is not None:
            return render_template("apology.html", top="Error", bottom="Username already exists"), 400

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
    return render_template("student_register.html")


@app.route("/student/login", methods=["GET", "POST"])
def student_login():
    """
    Allow existing students to log in (or redirect them!)
    """
    # When the login is successful, add the user type to the session
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")

        # Check the validity of the input
        if not username or not password:
            return render_template("apology.html", top="Error", bottom="Please provide a valid username and password"), 400

        # Check if the username exists and the password is correct
        student = Student.query.filter_by(username=username).first()
        if student is None or not check_password_hash(student.password, password):
            return render_template("apology.html", top="Error", bottom="Invalid username or password"), 400

        # Log in the user and store their ID and type in the session
        login_user(student)
        session['user_id'] = student.id
        session['user_type'] = 'student'
        session['user_name'] = student.username

        return redirect(url_for("student_dashboard"))
    return render_template("student_login.html")


@app.route("/teacher/register", methods=["GET", "POST"])
def teacher_register():
    """
    Allow new teachers to register for the platform
    """
    if request.method == "POST":
        username = request.form.get("username")
        email = request.form.get("email")
        password = request.form.get("password")
        confirmation = request.form.get("confirmation")

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
    return render_template("teacher_register.html")


@app.route("/teacher/login", methods=["GET", "POST"])
def teacher_login():
    """
    Allow existing teachers to log in!
    """
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")

        # Check the validity of the input
        if not username or not password:
            return render_template("apology.html", top="Error", bottom="Please provide a valid username and password"), 400

        # Check if the username exists and the password is correct
        teacher = Teacher.query.filter_by(username=username).first()
        if teacher is None or not check_password_hash(teacher.password, password):
            return render_template("apology.html", top="Error", bottom="Invalid username or password"), 400

        # Log in the user and store their info in the session
        login_user(teacher)
        session['user_id'] = teacher.id
        session['user_type'] = 'teacher'
        session['user_name'] = teacher.username

        return redirect(url_for("teacher_dashboard"))
    return render_template("teacher_login.html")


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
    """
    The main dashboard for teachers (this will show recent lesson records and schedules)
    """
    # Ensure the current user is a teacher
    if session['user_type'] != 'teacher':
        return redirect(url_for('index'))  # or wherever you want to redirect non-teachers

    # Fetch the most recent completed lesson record written by the logged-in teacher
    most_recent_record = LessonRecord.query.filter(
    and_(
        LessonRecord.teacher_id == session['user_id'],
        LessonRecord.date <= datetime.utcnow(),
        LessonRecord.lesson_summary.isnot(None)  # Add this line
    )
    ).options(
    joinedload(LessonRecord.student).joinedload(Student.profile)
    ).order_by(LessonRecord.date.desc()).first()
    
    # Fetch the upcoming lessons for the logged-in teacher
    upcoming_lessons = LessonRecord.query.filter(
        and_(
            LessonRecord.teacher_id == session['user_id'],
            LessonRecord.date >= datetime.utcnow()
        )
    ).options(
        joinedload(LessonRecord.student).joinedload(Student.profile)
    ).order_by(LessonRecord.date.asc()).all()

    # Render the teacher dashboard page
    return render_template('teacher/teacher_dashboard.html', profile=current_user.profile, most_recent_record=most_recent_record, upcoming_lessons=upcoming_lessons)


@app.route('/teacher/lesson_records')
@login_required
def teacher_lesson_records():
    """
    Show all the lesson records written by the logged-in teacher
    """
    if session['user_type'] != 'teacher':
        return redirect(url_for('home'))

    # Fetch the lesson records written by the logged-in teacher
    page = request.args.get('page', 1, type=int)
    lesson_records = LessonRecord.query.filter(
        and_(
            LessonRecord.teacher_id == session['user_id'],
            LessonRecord.date <= datetime.utcnow()
        )
    ).options(
        joinedload(LessonRecord.student).joinedload(Student.profile)
    ).order_by(LessonRecord.date.desc()).paginate(page=page, per_page=5)

    # Pass the lesson records to the template
    return render_template('/teacher/teacher_lesson_records.html', lesson_records=lesson_records)


@app.route('/teacher/edit_teacher_profile', methods=['GET', 'POST'])
@login_required
def edit_teacher_profile():
    """
    Where teachers can edit and update their own profiles
    """
    if request.method == 'POST':
        # Update teacher profile after form submission
        current_user.profile.age = request.form['age']
        current_user.profile.hobbies = request.form['hobbies']
        current_user.profile.motto = request.form['motto']
        current_user.profile.blood_type = request.form['blood_type']

        # Handle the image file separately because it's not a simple text field.
        image_file = request.files['image_file']
        if image_file:
            current_user.profile.image_file = save_image_file(image_file)

        db.session.commit()

    return render_template('teacher/edit_teacher_profile.html', profile=current_user.profile)


@app.route('/teacher/lesson_slots', methods=['GET', 'POST'])
@login_required
def manage_lesson_slots():
    if request.method == 'POST':
        start_time = datetime.strptime(request.form['start_time'], '%Y-%m-%dT%H:%M')
        end_time = datetime.strptime(request.form['end_time'], '%Y-%m-%dT%H:%M')
        new_slot = LessonSlot(teacher_id=current_user.id, start_time=start_time, end_time=end_time)
        db.session.add(new_slot)
        db.session.commit()
        flash('New lesson slot created!', 'success')

    # Get the start date of the week to display
    start_date_str = request.args.get('start_date')
    if start_date_str:
        start_date = datetime.strptime(start_date_str, '%Y-%m-%d')
    else:
        start_date = datetime.utcnow() - timedelta(days=datetime.utcnow().weekday())

    end_date = start_date + timedelta(days=6)
    lesson_slots = LessonSlot.query.filter(
        LessonSlot.teacher_id == current_user.id,
        LessonSlot.start_time >= start_date,
        LessonSlot.start_time <= end_date
    ).all()

    return render_template('teacher/lesson_slots.html', 
                           lesson_slots=lesson_slots, 
                           start_date=start_date,
                           end_date=end_date,
                           datetime=datetime, 
                           timedelta=timedelta)


@app.route('/teacher/update_slot', methods=['POST'])
@login_required
def update_lesson_slot():
    data = request.get_json()
    slot_id = data['slot_id']
    action = data['action']  # 'open' or 'close'

    if action == 'open':
        # Create new slot
        start_time = datetime.strptime(data['start_time'], '%Y-%m-%d %H:%M:%S')
        end_time = datetime.strptime(data['end_time'], '%Y-%m-%d %H:%M:%S')
        new_slot = LessonSlot(teacher_id=current_user.id, start_time=start_time, end_time=end_time, is_booked=False)
        db.session.add(new_slot)
        db.session.commit()
        return jsonify({'status': 'success', 'slot_id': new_slot.id})
    elif action == 'close':
        # Delete existing slot
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
    updates = []
    for item in data:
        if item['action'] == 'open':
            start_time = datetime.strptime(item['start_time'], '%Y-%m-%d %H:%M:%S')
            end_time = start_time + timedelta(minutes=59)
            new_slot = LessonSlot(teacher_id=current_user.id, start_time=start_time, end_time=end_time)
            db.session.add(new_slot)
            db.session.commit()
            updates.append({'action': 'open', 'slot_id': new_slot.id, 'start_time': start_time.strftime('%Y-%m-%d %H:%M:%S')})
        elif item['action'] == 'close':
            slot = LessonSlot.query.get(item['slot_id'])
            if slot:
                db.session.delete(slot)
                db.session.commit()
                updates.append({'action': 'close', 'slot_id': slot.id})
    return jsonify({'status': 'success', 'updates': updates})


@app.route('/student_profile/<int:student_id>', methods=['GET', 'POST'])
@login_required
def student_profile(student_id):
    """
    This route lets a teacher view and a student's profile.

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
    student = Student.query.get_or_404(student_id)

    if request.method == 'POST':
        form = request.form
        student.profile.hometown = form.get('hometown')
        student.profile.goal = form.get('goal')
        student.profile.hobbies = form.get('hobbies')
        student.profile.correction_style = form.get('correction_style')
        student.profile.english_weakness = form.get('english_weakness')
        db.session.commit()
        # Redirect to the same page to show the updated profile
        return redirect(url_for('student_profile', student_id=student_id))

    # Pass the student's profile to the template
    return render_template('view_student_profile.html', student=student)


@app.route('/edit_student_profile/<int:student_id>', methods=['GET', 'POST'])
@login_required
def edit_student_profile_by_teacher(student_id):
    """
    This route lets a teacher edit a student's profile.
    Non-teachers are redirected to the login page.
    If the student doesn't have a profile, a new one is created.
    On a POST request, the student's profile is updated with form data and saved to the database.
    The 'view_student_profile.html' template is rendered, displaying the student's profile.
    """
    if 'user_type' not in session or session['user_type'] != 'teacher':
        # The student is not logged in or is not a teacher. Redirect them to the login page.
        return redirect(url_for('login'))

    student = User.query.get_or_404(student_id)

    if student.profile is None:
        # Create a new StudentProfile for the student
        profile = StudentProfile(student_id=student.id, image_file='default.jpg')
        db.session.add(profile)
        db.session.commit()
        student.profile = profile

    if request.method == 'POST':
        # Updates the student's profile.
        student.profile.hometown = request.form['hometown']
        student.profile.goal = request.form['goal']
        student.profile.hobbies = request.form['hobbies']
        student.profile.correction_style = request.form['correction_style']
        student.profile.english_weakness = request.form['english_weakness']

        db.session.commit()

    return render_template('view_student_profile.html', profile=student.profile)


# Student Only Routes
@app.route('/student/dashboard')
def student_dashboard():
    if session['user_type'] != 'student':
        return redirect(url_for('home'))

    # Fetch the most recent lesson record for the logged-in student
    most_recent_record = LessonRecord.query.filter_by(student_id=session['user_id']).options(
        joinedload(LessonRecord.teacher).joinedload(Teacher.profile)
    ).order_by(LessonRecord.date.desc()).first()

    # Fetch all upcoming lesson records for the logged-in student
    upcoming_lessons = LessonRecord.query.filter(
        LessonRecord.student_id==session['user_id'],
        LessonRecord.date>=datetime.now()
    ).options(
        joinedload(LessonRecord.teacher).joinedload(Teacher.profile)
    ).order_by(LessonRecord.date.asc()).all()

    # Pass the most recent record, the upcoming lessons, and the profile to the template
    return render_template('student/student_dashboard.html', profile=current_user.profile, most_recent_record=most_recent_record, upcoming_lessons=upcoming_lessons)


@app.route('/cancel_lesson', methods=['POST'])
def cancel_lesson():
    if session['user_type'] != 'student':
        return redirect(url_for('home'))

    # Get the ID of the lesson to be cancelled from the form data
    lesson_id = request.form.get('lesson_id')

    # Fetch the lesson record from the database
    lesson = LessonRecord.query.get(lesson_id)

    # Check if the lesson exists and belongs to the logged-in student
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


@app.route('/student/lesson_records')
def student_lesson_records():
    # Fetch all lesson records for the logged-in student
    page = request.args.get('page', 1, type=int)
    lesson_records = LessonRecord.query.filter_by(student_id=session['user_id']).options(
        joinedload(LessonRecord.teacher).joinedload(Teacher.profile)
    ).order_by(LessonRecord.date.desc()).paginate(page=page, per_page=5)

    # Pass the lesson records to the template
    return render_template('student/lesson_records.html', lesson_records=lesson_records)


@app.route('/student/edit_student_profile', methods=['GET', 'POST'])
@login_required
def edit_student_profile():
    if 'user_type' not in session or session['user_type'] != 'student':
        # The user is not logged in or is not a student. Redirect them to the login page.
        return redirect(url_for('login'))
    
    if current_user.profile is None:
        # Create a new StudentProfile for the current_user
        profile = StudentProfile(student_id=current_user.id, image_file='default.jpg')
        db.session.add(profile)
        db.session.commit()
        current_user.profile = profile
    
    if request.method == 'POST':
        # The form has been submitted. Update the student's profile.
        current_user.profile.hometown = request.form['hometown']
        current_user.profile.goal = request.form['goal']
        current_user.profile.hobbies = request.form['hobbies']
        current_user.profile.correction_style = request.form['correction_style']
        current_user.profile.english_weakness = request.form['english_weakness']
        
        # Handle the image file separately because it's not a simple text field.
        image_file = request.files['image_file']
        if image_file:
            # Save the image file somewhere and update the profile's image_file field.
            current_user.profile.image_file = save_image_file(image_file)

        db.session.commit()

    # Render the edit profile page.
    return render_template('student/edit_student_profile.html', profile=current_user.profile)


@app.route('/student/book_lesson', methods=['GET', 'POST'])
@login_required
def student_book_lesson():
    """
    This route allows students to book a lesson slot with a Teacher.
    """
    if request.method == 'POST':
        lesson_slot_id = request.form.get('lesson_slot')
        teacher_id = request.form.get('teacher')

        # Fetch the lesson slot
        lesson_slot = LessonSlot.query.get(lesson_slot_id)

        # Check if the lesson slot exists and is not already booked
        if not lesson_slot or lesson_slot.is_booked:
            flash('Lesson slot is not available', 'error')
            return redirect(url_for('student_dashboard'))

        # Fetch the current student
        student = Student.query.get(current_user.id)

        # Check if the student has enough lessons purchased
        if student.lessons_purchased <= student.number_of_lessons:
            flash('Not enough lessons purchased', 'error')
            return redirect(url_for('student_dashboard'))

        # Create a new booking
        booking = Booking(student_id=student.id, lesson_slot_id=lesson_slot.id)
        db.session.add(booking)

        # Update the lesson slot and student
        lesson_slot.is_booked = True
        student.number_of_lessons += 1

        # Create a new lesson record
        lesson_record = LessonRecord(
            student_id=current_user.id,
            teacher_id=teacher_id,
            date=lesson_slot.start_time.date()
        )
        db.session.add(lesson_record)

        # Commit the changes to the database
        db.session.commit()

        flash('Lesson booked successfully', 'success')
        return redirect(url_for('student_dashboard'))
    else:  # GET request
        # Fetch all available lesson slots
        available_lesson_slots = LessonSlot.query.filter_by(is_booked=False).all()

        # Pass the available lesson slots to the template
        return render_template('student/book_lesson.html', lesson_slots=available_lesson_slots)
    

if __name__ == '__main__':
    app.run(debug=True)