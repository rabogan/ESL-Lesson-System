import os
import secrets
import json
from flask import Flask, current_app, session, render_template, request, redirect, url_for, flash
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import types
from sqlalchemy.orm import joinedload
from flask_migrate import Migrate
from datetime import datetime
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
    profile = db.relationship('StudentProfile', uselist=False, back_populates='student')
    lesson_records = db.relationship('LessonRecord', back_populates='student')

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

# Temporary test of 'students'
@app.route("/students", methods=["GET"])
def get_students():
    page = request.args.get('page', 1, type=int)
    students = Student.query.paginate(page=page, per_page=5)
    return render_template("students.html", students=students)

# Temporary test of 'teachers'
@app.route("/teachers", methods=["GET"])
def get_teachers():
    page = request.args.get('page', 1, type=int)
    teachers = Teacher.query.paginate(page=page, per_page=5)
    return render_template("teachers.html", teachers=teachers)

# Temporary Viewing Of 'Lesson Records'
@app.route("/lessons", methods=["GET"])
def get_lessons():
    page = request.args.get('page', 1, type=int)
    lessons = LessonRecord.query.paginate(page=page, per_page=5)
    return render_template("lessons.html", lessons=lessons)

@app.route('/portal_choice')
def portal_choice():
    return render_template('portal_choice.html')

@app.route('/logout')
def logout():
    logout_user()
    session.pop('user_id', None)
    session.pop('user_type', None)
    flash('You were logged out')
    return redirect(url_for('index'))

@app.route("/student/register", methods=["GET", "POST"])
def student_register():
    if request.method == "POST":
        username = request.form.get("username")
        email = request.form.get("email")
        password = request.form.get("password")
        confirmation = request.form.get("confirmation")

        # Check the validity of the input
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
        
        # Create a new StudentProfile for the newly registered teacher
        profile = StudentProfile(student_id=new_student.id, image_file='default1.jpg')
        db.session.add(profile)
        db.session.commit()

        # Store the user ID in the session
        session['user_id'] = new_student.id
        session['user_type'] = 'student'
        session['user_name'] = new_student.username  # Add this line

        return redirect(url_for("student_login"))
    return render_template("student_register.html")

@app.route("/student/login", methods=["GET", "POST"])
def student_login():
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

        return redirect(url_for("index"))  # Redirect to a main page after login
    return render_template("student_login.html")

@app.route("/teacher/register", methods=["GET", "POST"])
def teacher_register():
    if request.method == "POST":
        username = request.form.get("username")
        email = request.form.get("email")
        password = request.form.get("password")
        confirmation = request.form.get("confirmation")

        # Check the validity of the input
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

        # Store the user ID in the session
        session['user_id'] = new_teacher.id
        session['user_type'] = 'teacher'
        session['user_name'] = new_teacher.username

        return redirect(url_for("teacher_login"))
    return render_template("teacher_register.html")

@app.route("/teacher/login", methods=["GET", "POST"])
def teacher_login():
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

        # Log in the user and store their ID and type in the session
        login_user(teacher)
        session['user_id'] = teacher.id
        session['user_type'] = 'teacher'
        session['user_name'] = teacher.username

        return redirect(url_for("index"))  # Redirect to a main page after login
    return render_template("teacher_login.html")

@app.route("/")
def index():
    return render_template("display.html")


@app.route('/meetYourTeacher')
def meet_your_teacher():
    page = request.args.get('page', 1, type=int)
    teachers = Teacher.query.paginate(page=page, per_page=6)
    return render_template('meetYourTeacher.html', teachers=teachers)

@app.route('/edit_teacher_profile', methods=['GET', 'POST'])
@login_required
def edit_teacher_profile():
    if request.method == 'POST':
        # The form has been submitted. Update the teacher's profile.
        current_user.profile.age = request.form['age']
        current_user.profile.hobbies = request.form['hobbies']
        current_user.profile.motto = request.form['motto']
        current_user.profile.blood_type = request.form['blood_type']

        # Handle the image file separately because it's not a simple text field.
        image_file = request.files['image_file']
        if image_file:
            # Save the image file somewhere and update the profile's image_file field.
            # This is just a placeholder. You'll need to implement the actual image saving.
            current_user.profile.image_file = save_image_file(image_file)

        db.session.commit()

    # Render the edit profile page.
    return render_template('edit_teacher_profile.html', profile=current_user.profile)


# Function to save the image file
def save_image_file(image_file):
    # Generate a random hex for the filename to ensure it's unique
    random_hex = secrets.token_hex(8)
    _, file_extension = os.path.splitext(image_file.filename)
    new_filename = random_hex + file_extension

    # Determine the directory based on the user type
    if session['user_type'] == 'teacher':
        directory = 'static/img/teacherImg'
        default_image = 'default.jpg'
    elif session['user_type'] == 'student':
        directory = 'static/img/studentImg'
        default_image = 'default1.png'
    else:
        return None  # Or handle this case differently

    # Build the full file path
    image_path = os.path.join(current_app.root_path, directory, new_filename)

    # Save the file
    image_file.save(image_path)

    # Delete the old image file, if it exists and is not the default image
    old_image_path = os.path.join(current_app.root_path, directory, current_user.profile.image_file)
    if os.path.exists(old_image_path) and current_user.profile.image_file != default_image:
        os.remove(old_image_path)

    return new_filename


@app.route('/teacher_dashboard')
@login_required
def teacher_dashboard():
    # Ensure the current user is a teacher
    if session['user_type'] != 'teacher':
        return redirect(url_for('home'))  # or wherever you want to redirect non-teachers

    # Fetch the most recent lesson record written by the logged-in teacher
    most_recent_record = LessonRecord.query.filter_by(teacher_id=session['user_id']).options(
        joinedload(LessonRecord.student).joinedload(Student.profile)
    ).order_by(LessonRecord.date.desc()).first()

    # Render the teacher dashboard page
    return render_template('teacher_dashboard.html', profile=current_user.profile, most_recent_record=most_recent_record)


@app.route('/teacher/lesson_records')
@login_required
def teacher_lesson_records():
    # Ensure the current user is a teacher
    if session['user_type'] != 'teacher':
        return redirect(url_for('home'))

    # Fetch the lesson records written by the logged-in teacher
    page = request.args.get('page', 1, type=int)
    lesson_records = LessonRecord.query.filter_by(teacher_id=session['user_id']).options(
        joinedload(LessonRecord.student).joinedload(Student.profile)
    ).order_by(LessonRecord.date.desc()).paginate(page=page, per_page=5)

    # Pass the lesson records to the template
    return render_template('teacher_lesson_records.html', lesson_records=lesson_records)



@app.route('/student/dashboard')
def student_dashboard():
    # Your code here
    if session['user_type'] != 'student':
        return redirect(url_for('home'))

    # Fetch the most recent lesson record for the logged-in student
    most_recent_record = LessonRecord.query.filter_by(student_id=session['user_id']).options(
        joinedload(LessonRecord.teacher).joinedload(Teacher.profile)
    ).order_by(LessonRecord.date.desc()).first()

    # Pass the most recent record and the profile to the template
    return render_template('student_dashboard.html', profile=current_user.profile, most_recent_record=most_recent_record)


@app.route('/student/lesson_records')
def lesson_records():
    # Fetch all lesson records for the logged-in student
    page = request.args.get('page', 1, type=int)
    lesson_records = LessonRecord.query.filter_by(student_id=session['user_id']).options(
        joinedload(LessonRecord.teacher).joinedload(Teacher.profile)
    ).order_by(LessonRecord.date.desc()).paginate(page=page, per_page=5)

    # Pass the lesson records to the template
    return render_template('lesson_records.html', lesson_records=lesson_records)


@app.route('/edit_student_profile', methods=['GET', 'POST'])
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
    return render_template('edit_student_profile.html', profile=current_user.profile)


@app.route('/edit_student_profile/<int:student_id>', methods=['GET', 'POST'])
@login_required
def edit_student_profile_by_teacher(student_id):
    if 'user_type' not in session or session['user_type'] != 'teacher':
        # The user is not logged in or is not a teacher. Redirect them to the login page.
        return redirect(url_for('login'))

    student = User.query.get_or_404(student_id)

    if student.profile is None:
        # Create a new StudentProfile for the student
        profile = StudentProfile(student_id=student.id, image_file='default.jpg')
        db.session.add(profile)
        db.session.commit()
        student.profile = profile

    if request.method == 'POST':
        # The form has been submitted. Update the student's profile.
        student.profile.hometown = request.form['hometown']
        student.profile.goal = request.form['goal']
        student.profile.hobbies = request.form['hobbies']
        student.profile.correction_style = request.form['correction_style']
        student.profile.english_weakness = request.form['english_weakness']

        db.session.commit()

    # Render the edit profile page.
    return render_template('student_profile.html', profile=student.profile)


@app.route('/student_profile/<int:student_id>', methods=['GET', 'POST'])
@login_required
def student_profile(student_id):
    # Ensure the current user is a teacher
    if session['user_type'] != 'teacher':
        return redirect(url_for('home'))

    # Fetch the student's profile
    student = Student.query.get_or_404(student_id)

    if request.method == 'POST':
        # Handle the POST request here
        # For example, update the student's profile with the data from the form
        form = request.form
        student.profile.hometown = form.get('hometown')
        student.profile.goal = form.get('goal')
        student.profile.hobbies = form.get('hobbies')
        student.profile.correction_style = form.get('correction_style')
        student.profile.english_weakness = form.get('english_weakness')
        # Save the changes to the database
        db.session.commit()
        # Redirect to the same page to show the updated profile
        return redirect(url_for('student_profile', student_id=student_id))

    # Pass the student's profile to the template
    return render_template('student_profile.html', student=student)


if __name__ == '__main__':
    app.run(debug=True)