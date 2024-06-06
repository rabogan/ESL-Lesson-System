import json
import pytz
import logging
from flask import Flask, session, render_template, request, redirect, url_for, flash, jsonify
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from sqlalchemy.orm import joinedload
from datetime import datetime, timedelta, timezone
from flask_wtf import CSRFProtect
from flask_limiter import Limiter
from helpers.auth_helpers import authenticate_user, create_user, create_profile, login_new_user, is_username_taken
from helpers.time_helpers import convert_to_utc, ensure_timezone_aware, get_week_boundaries, get_user_timezone
from helpers.file_helpers import save_image_file
from helpers.form_helpers import process_form_data
from helpers.lesson_record_helpers import get_paginated_lesson_records, make_times_timezone_aware
from helpers.student_helpers import update_student_profile, get_student_by_id
from helpers.teacher_helpers import get_outstanding_lessons, get_teacher_by_id, get_teacher_profile_by_id, get_most_recent_lesson_record, get_upcoming_lessons, update_teacher_profile
from models import db, Student, StudentProfile, Teacher, TeacherProfile, LessonRecord, LessonSlot, Booking
from forms import RegistrationForm, LoginForm, EditTeacherProfileForm, StudentProfileForm, TeacherEditsStudentForm, LessonRecordForm, LessonSlotsForm, StudentLessonSlotForm, CancelLessonForm
from database import db, migrate


# Initialize Flask app
app = Flask(__name__)
app.secret_key = 'coolie_killer_huimin_himitsunakotogawaruidesune'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///site.db'
app.config['DEBUG'] = True
app.logger.setLevel(logging.INFO)


# Initialize extensions
db.init_app(app)
migrate.init_app(app, db)
login_manager = LoginManager()
login_manager.init_app(app)
csrf = CSRFProtect(app)
csrf.init_app(app)
limiter = Limiter(app)


# Set up logging
logging.basicConfig(level=logging.DEBUG)


# Ensure database tables are created
with app.app_context():
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
    This route (GET /teacher_profile/<int:teacher_id>) displays a teacher's profile.
    It is a public view and not editable.
    The route expects an integer `teacher_id` as a parameter in the URL.
    It returns an HTML response with the teacher's profile, or a 404 error if the teacher or profile is not found.
    """
    # Fetch the teacher
    teacher = get_teacher_by_id(teacher_id)
    if teacher is None:
        app.logger.error(f"Teacher with ID {teacher_id} not found.")
        return render_template('404.html'), 404

    # Fetch the teacher's profile
    profile = get_teacher_profile_by_id(teacher_id)
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
    Handles the registration of a new student, rate-limited to 5 requests per minute to prevent abuse.
    It uses a RegistrationForm to validate the submitted data. If the form data is valid,
    it checks if a student with the submitted username already exists. If the username is taken,
    it adds an error to the form and re-renders the registration page with a 400 status.

    If the username is not taken, it creates a new Student with the submitted data and a hashed password,
    and adds it to the database. It then creates a new StudentProfile for the newly registered student
    with a default image, and adds it to the database.

    If the form data is not valid, it simply renders the registration page with the form.
    """
    form = RegistrationForm()
    
    if form.validate_on_submit():
        username = form.username.data
        email = form.email.data
        password = form.password.data

        if is_username_taken(Student, username):
            form.username.errors.append("Username already exists")
            return render_template("student_register.html", form=form), 400

        new_student = create_user(Student, username, email, password)
        create_profile(StudentProfile, new_student.id, 'default1.jpg')
        login_new_user(new_student, 'student')

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

        if not username or not password:
            return render_template("apology.html", top="Error", bottom="Please provide a valid username and password"), 400

        student = authenticate_user(Student, username, password)
        if student is None:
            return render_template("apology.html", top="Error", bottom="Invalid username or password"), 400

        login_new_user(student, 'student')
        login_user(student, remember)

        return redirect(url_for("student_dashboard"))
    return render_template("student_login.html", form=form)

@app.route("/teacher/register", methods=["GET", "POST"])
@limiter.limit("5/minute")
def teacher_register():
    """
    Creates a new teacher account and profile, then logs in the new teacher.
    See /student/register for more details on how this works, as it's very similar.
    This obeys the DRY principle in that regard!
    """
    form = RegistrationForm()
    
    if form.validate_on_submit():
        username = form.username.data
        email = form.email.data
        password = form.password.data

        if is_username_taken(Teacher, username) or is_username_taken(Teacher, email):
            return render_template("apology.html", top="Error", bottom="Registration error"), 400

        new_teacher = create_user(Teacher, username, email, password)
        create_profile(TeacherProfile, new_teacher.id, 'default.jpg')
        login_new_user(new_teacher, 'teacher')

        return redirect(url_for("teacher_dashboard"))
    
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

        if not username or not password:
            return render_template("apology.html", top="Error", bottom="Please provide a valid username and password"), 400

        teacher = authenticate_user(Teacher, username, password)
        if teacher is None:
            return render_template("apology.html", top="Error", bottom="Invalid username or password"), 400

        login_new_user(teacher, 'teacher')
        login_user(teacher, remember=remember)

        return redirect(url_for("teacher_dashboard"))
    return render_template("teacher_login.html", form=form)


@app.route('/logout')
@login_required
def logout():
    """
    Log out the user and clear the session
    """
    logout_user()
    session.pop('user_id', None)
    session.pop('user_type', None)
    return redirect(url_for('index'))


# Teacher Only Routes
@app.route('/teacher/teacher_dashboard')
@login_required
def teacher_dashboard():
    """
    A means of allowing easy schedule management: showing teachers their upcoming lessons and outstanding lesson records.
    """
    # Ensure the current user is a teacher
    if session['user_type'] != 'teacher':
        return redirect(url_for('index'))

    teacher_id = session['user_id']
    teacher = Teacher.query.get(teacher_id)
    if teacher is None:
        app.logger.error(f"Teacher with ID {teacher_id} not found.")
        return render_template('404.html'), 404

    user_timezone = teacher.timezone

    # Fetch the most recent lesson record and upcoming lessons
    most_recent_record = get_most_recent_lesson_record(teacher_id, user_timezone)
    upcoming_lessons = get_upcoming_lessons(teacher_id, user_timezone)
    outstanding_lessons = get_outstanding_lessons(teacher_id, user_timezone)
    
    # Pass the user_timezone to the template
    return render_template('teacher/teacher_dashboard.html', profile=current_user.profile, most_recent_record=most_recent_record, upcoming_lessons=upcoming_lessons, outstanding_lessons=outstanding_lessons, user_timezone=user_timezone)


@app.route('/teacher/lesson_records')
@login_required
def teacher_lesson_records():
    if session['user_type'] != 'teacher':
        return redirect(url_for('home'))

    teacher = get_teacher_by_id(session['user_id'])
    if not teacher:
        app.logger.error(f"Teacher with ID {session['user_id']} not found.")
        return render_template('404.html'), 404
    
    page = request.args.get('page', 1, type=int)
    lesson_records = get_paginated_lesson_records(teacher.id, page, 'teacher')
    lesson_records = make_times_timezone_aware(lesson_records, teacher.timezone)

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
        update_teacher_profile(current_user.profile, form)
        return redirect(url_for('edit_teacher_profile', updated=True))

    return render_template('teacher/edit_teacher_profile.html', form=form, profile=current_user.profile, profile_updated=profile_updated)


@app.route('/teacher/lesson_slots', methods=['GET'])
@login_required
def manage_lesson_slots():
    form = LessonSlotsForm()
    teacher = db.session.get(Teacher, current_user.id)
    user_timezone = pytz.timezone(teacher.timezone)
    print(f"User timezone: {user_timezone}")

    week_offset = int(request.args.get('week_offset', 0))
    today = datetime.now(user_timezone)
    print(f"Today's date: {today}")

    start_of_week = today - timedelta(days=today.weekday(), hours=today.hour, minutes=today.minute, seconds=today.second, microseconds=today.microsecond) + timedelta(weeks=week_offset)
    end_of_week = start_of_week + timedelta(days=6, hours=23, minutes=59)
    start_of_week_utc = start_of_week.astimezone(timezone.utc)
    end_of_week_utc = end_of_week.astimezone(timezone.utc)
    print(f"Start of week: {start_of_week}, End of week: {end_of_week}")
    print(f"Start of week (UTC): {start_of_week_utc}, End of week (UTC): {end_of_week_utc}")

    with db.session.no_autoflush:
        lesson_slots = LessonSlot.query.filter(
            LessonSlot.teacher_id == current_user.id,
            LessonSlot.start_time >= start_of_week_utc,
            LessonSlot.start_time <= end_of_week_utc
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
def manage_slot(start_time_str, end_time_str, teacher_id, timezone_str, action):
    # Convert the provided start and end time strings to datetime objects
    local_start_time = datetime.strptime(start_time_str, '%Y-%m-%dT%H:%M')
    local_end_time = datetime.strptime(end_time_str, '%Y-%m-%dT%H:%M')

    # Localize the times to the specified timezone and convert to UTC
    timezone = pytz.timezone(timezone_str)
    start_time = timezone.localize(local_start_time).astimezone(pytz.UTC)
    end_time = timezone.localize(local_end_time).astimezone(pytz.UTC)

    # Query for an existing slot with the same start and end times
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
    start_time = ensure_timezone_aware(start_time, timezone).astimezone(pytz.UTC)
    end_time = ensure_timezone_aware(end_time, timezone).astimezone(pytz.UTC)
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
        start_time = user_timezone.localize(local_start_time).astimezone(pytz.UTC)
        end_time = user_timezone.localize(local_end_time).astimezone(pytz.UTC)
        return jsonify(open_slot(start_time, end_time, current_user.id, user_timezone))
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
    app.logger.info(f"Editing lesson with ID {lesson_id}")
    
    if session['user_type'] != 'teacher':
        app.logger.info("User is not a teacher")
        return redirect(url_for('index'))

    lesson = db.session.query(LessonRecord).get(lesson_id)
    if lesson is None:
        app.logger.error(f"Lesson with ID {lesson_id} not found.")
        return render_template('404.html'), 404

    form = LessonRecordForm(obj=lesson)
    if request.method == 'GET':
        form.new_words.data = json.dumps(lesson.new_words)
        form.new_phrases.data = json.dumps(lesson.new_phrases)
        app.logger.info(f"Pre-populated form data: new_words={form.new_words.data}, new_phrases={form.new_phrases.data}")
    
    app.logger.info(f"CSRF token when rendering form: {form.csrf_token.data}")
    if form.validate_on_submit():
        app.logger.info("Form validated successfully")
        lesson.lesson_summary = form.lesson_summary.data
        lesson.strengths = form.strengths.data
        lesson.areas_to_improve = form.areas_to_improve.data
        lesson.new_words = process_form_data(form.new_words.data)
        lesson.new_phrases = process_form_data(form.new_phrases.data)

        teacher = db.session.get(Teacher, session['user_id'])
        if teacher is None:
            app.logger.error(f"Teacher with ID {session['user_id']} not found.")
            return render_template('404.html'), 404
        lesson.lastEditTime = convert_to_utc(datetime.now(timezone.utc), teacher.timezone)
    
        db.session.commit()
        app.logger.info("Lesson updated successfully")
        flash('Lesson updated successfully!', 'success')
        return redirect(url_for('teacher_dashboard'))
    else:
        app.logger.error(f"Form validation failed: {form.errors}")
        app.logger.error(f"Form data: {form.data}")
        app.logger.error(f"CSRF token: {form.csrf_token.data}")
        flash('There was an error updating the lesson. Please check your input.', 'error')
        
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
    student = get_student_by_id(session['user_id'])

    if student is None:
        app.logger.error(f"Student with ID {session['user_id']} not found.")
        return render_template('404.html'), 404
    
    user_timezone = get_user_timezone(student.timezone)

    # Fetch all past lesson records for the logged-in student
    page = request.args.get('page', 1, type=int)
    lesson_records = get_paginated_lesson_records(student.id, page, 'student')
    lesson_records = make_times_timezone_aware(lesson_records, student.timezone)
            
    return render_template('student/lesson_records.html', lesson_records=lesson_records, user_timezone=user_timezone)


@app.route('/student/edit_student_profile', methods=['GET', 'POST'])
@login_required
def edit_student_profile():
    if session.get('user_type') != 'student':
        return redirect(url_for('login'))
    
    # Ensure the student profile exists
    if current_user.profile is None:
        profile = StudentProfile(student_id=current_user.id, image_file='default1.png')
        db.session.add(profile)
        db.session.commit()
        current_user.profile = profile
    
    form = StudentProfileForm(obj=current_user.profile)
    
    if form.validate_on_submit():
        update_student_profile(form, current_user.profile)
        if form.image_file.data:
            current_user.profile.image_file = save_image_file(form.image_file.data)
        
        db.session.commit()
        return redirect(url_for('edit_student_profile', updated=True))
    
    profile_updated = request.args.get('updated', False)
    return render_template('student/edit_student_profile.html', form=form, profile=current_user.profile, profile_updated=profile_updated)


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
        LessonSlot.start_time >= current_time_utc
    ).all()

    slots_dict = [{'id': slot.id, 'time': slot.start_time.replace(tzinfo=timezone.utc).astimezone(user_timezone).strftime('%Y-%m-%d %I:%M %p'), 'teacher': slot.teacher.username} for slot in slots]
    return jsonify(slots_dict)


@app.teardown_appcontext
def shutdown_session(exception=None):
    db.session.remove()


if __name__ == '__main__':
    app.run(debug=True)