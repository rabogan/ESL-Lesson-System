import logging
import pytz
from datetime import datetime
from flask import Flask, session, render_template, request, redirect, url_for, flash, jsonify
from flask_login import LoginManager, logout_user, login_required, current_user
from flask_wtf import CSRFProtect
from flask_limiter import Limiter
from helpers.auth_helpers import register_user, login_user_helper
from helpers.dashboard_helpers import get_most_recent_lesson_record, get_upcoming_lessons
from helpers.edit_lesson_record_helpers import get_lesson_by_id, initialize_lesson_form, update_lesson_from_form, update_last_edit_time
from helpers.file_helpers import save_image_file
from helpers.lesson_record_helpers import get_paginated_lesson_records, make_times_timezone_aware
from helpers.student_helpers import update_student_profile, get_student_by_id, cancel_student_lesson
from helpers.student_booking_helpers import fetch_available_slots, convert_slots_to_dict, update_student_booking, fetch_and_format_slots
from helpers.teacher_helpers import get_outstanding_lessons, get_teacher_by_id, get_teacher_profile_by_id, update_teacher_profile, update_student_profile_from_form
from helpers.teacher_lesson_slot_mgmt_helpers import open_slot, close_slot, get_lesson_slots_for_week
from helpers.time_helpers import ensure_timezone_aware, get_week_boundaries, get_user_timezone
from models import Student, StudentProfile, Teacher, LessonSlot
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
    Displays the index page of our web app, 
    """
    return render_template("display.html")


@app.route('/meetYourTeachers')
def meet_your_teacher():
    """
    Shows a rogue's gallery of all the teachers present in the system
    """
    page = request.args.get('page', 1, type=int)
    teachers = Teacher.query.paginate(page=page, per_page=6)
    return render_template('meetYourTeachers.html', teachers=teachers)


@app.route('/ourLessons')
def our_lessons():
    """
    This page provides information about the lessons offered.
    """
    return render_template('ourLessons.html')


@app.route('/developerProfile')
def developer_profile():
    """
    This page provides contact information for the school.
    """
    return render_template('developerProfile.html')


@app.route('/teacherProfile/<int:teacher_id>', methods=['GET'])
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
    return render_template('viewTeacherProfile.html', teacher=teacher, profile=profile)


@app.route('/portalChoice')
def portal_choice():
    """
    This is where the user chooses whether to log in/register as a student or teacher.
    """
    return render_template('portalChoice.html')


@app.route("/student/register", methods=["GET", "POST"])
@limiter.limit("5/minute")
def student_register():
    form = RegistrationForm()
    
    if form.validate_on_submit():
        new_user, error_message = register_user(form, 'student')
        if error_message:
            form.username.errors.append(error_message)
            return render_template("studentRegister.html", form=form), 400
        return redirect(url_for("student_dashboard"))
    
    return render_template("studentRegister.html", form=form)

@app.route("/student/login", methods=["GET", "POST"])
@limiter.limit("5/minute")
def student_login():
    form = LoginForm()
    if form.validate_on_submit():
        user, error_message = login_user_helper(form, Student, 'student')
        if error_message:
            return render_template("apology.html", top="Error", bottom=error_message), 400
        return redirect(url_for("student_dashboard"))
    return render_template("studentLogin.html", form=form)


@app.route("/teacher/register", methods=["GET", "POST"])
@limiter.limit("5/minute")
def teacher_register():
    form = RegistrationForm()
    if form.validate_on_submit():
        new_user, error_message = register_user(form, 'teacher')
        if error_message:
            return render_template("apology.html", top="Error", bottom=error_message), 400
        return redirect(url_for("teacher_dashboard"))
    
    return render_template("teacherRegister.html", form=form)


@app.route("/teacher/login", methods=["GET", "POST"])
@limiter.limit("5/minute")
def teacher_login():
    form = LoginForm()
    if form.validate_on_submit():
        user, error_message = login_user_helper(form, Teacher, 'teacher')
        if error_message:
            return render_template("apology.html", top="Error", bottom=error_message), 400
        return redirect(url_for("teacher_dashboard"))
    return render_template("teacherLogin.html", form=form)


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
@app.route('/teacher/dashboard')
@login_required
def teacher_dashboard():
    if session.get('user_type') != 'teacher':
        return redirect(url_for('index'))

    teacher = get_teacher_by_id(session['user_id'])
    if not teacher:
        app.logger.error(f"Teacher with ID {session['user_id']} not found.")
        return render_template('404.html'), 404

    user_timezone = teacher.timezone

    most_recent_record = get_most_recent_lesson_record(teacher.id, 'teacher', user_timezone)
    upcoming_lessons = get_upcoming_lessons(teacher.id, 'teacher', user_timezone)
    outstanding_lessons = get_outstanding_lessons(teacher.id, user_timezone)

    return render_template('teacher/teacherDashboard.html', profile=current_user.profile, most_recent_record=most_recent_record, upcoming_lessons=upcoming_lessons, outstanding_lessons=outstanding_lessons, user_timezone=user_timezone)


@app.route('/teacher/lessonRecords')
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

    return render_template('teacher/teacherLessonRecords.html', lesson_records=lesson_records)


@app.route('/teacher/editTeacherProfile', methods=['GET', 'POST'])
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

    return render_template('teacher/editTeacherProfile.html', form=form, profile=current_user.profile, profile_updated=profile_updated)


@app.route('/teacher/lessonSlots', methods=['GET'])
@login_required
def manage_lesson_slots():
    form = LessonSlotsForm()
    teacher = db.session.get(Teacher, current_user.id)
    user_timezone = get_user_timezone(teacher.timezone)
    
    week_offset = int(request.args.get('week_offset', 0))
    start_of_week_utc, end_of_week_utc = get_week_boundaries(teacher.timezone, week_offset)

    lesson_slots = get_lesson_slots_for_week(current_user.id, start_of_week_utc, end_of_week_utc)
    
    utc_now = datetime.now(pytz.UTC)
    lesson_slots_json = [{
        'slot_id': slot.id,
        'start_time': slot.start_time.astimezone(user_timezone).isoformat(),
        'end_time': slot.end_time.astimezone(user_timezone).isoformat(),
        'status': 'Booked' if slot.is_booked else 'Available' if slot.start_time.astimezone(pytz.UTC) > utc_now else 'Closed'
    } for slot in lesson_slots]

    app.logger.info(f"Returning lesson slots: {lesson_slots_json}")

    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return jsonify(lesson_slots_json)
    else:
        return render_template('teacher/lessonSlots.html', form=form)

@app.route('/teacher/updateSlot', methods=['POST'])
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

@app.route('/updateSlotStatus', methods=['POST'])
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

@app.route('/teacher/updateSlots', methods=['POST'])
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

@app.route('/studentProfile/<int:student_id>', methods=['GET', 'POST'])


@app.route('/studentProfile/<int:student_id>', methods=['GET', 'POST'])
@login_required 
def student_profile(student_id):
    if session['user_type'] != 'teacher':
        return redirect(url_for('index'))

    student = db.session.get(Student, student_id)
    if student is None:
        flash('Student not found', 'error')
        return render_template('404.html'), 404

    form = TeacherEditsStudentForm(obj=student.profile)
    profile_updated = request.args.get('updated', False)

    if form.validate_on_submit():
        success = update_student_profile_from_form(student.profile, form)
        if success:
            flash('Profile updated successfully', 'success')
        else:
            flash('Error updating profile', 'error')
        return redirect(url_for('student_profile', student_id=student.id, updated=True))

    return render_template('viewStudentProfile.html', form=form, student=student, profile_updated=profile_updated)


@app.route('/teacher/editLesson/<int:lesson_id>', methods=['GET', 'POST'])
@login_required
def edit_lesson(lesson_id):
    app.logger.info(f"Editing lesson with ID {lesson_id}")
    
    if session['user_type'] != 'teacher':
        app.logger.info("User is not a teacher")
        return redirect(url_for('index'))

    lesson = get_lesson_by_id(lesson_id)
    if lesson is None:
        app.logger.error(f"Lesson with ID {lesson_id} not found.")
        return render_template('404.html'), 404

    form = LessonRecordForm(obj=lesson)
    if request.method == 'GET':
        initialize_lesson_form(form, lesson)
        app.logger.info(f"Pre-populated form data: new_words={form.new_words.data}, new_phrases={form.new_phrases.data}")

    app.logger.info(f"CSRF token when rendering form: {form.csrf_token.data}")
    if form.validate_on_submit():
        app.logger.info("Form validated successfully")
        update_lesson_from_form(lesson, form)
        
        try:
            update_last_edit_time(lesson, session['user_id'])
        except ValueError as e:
            app.logger.error(e)
            return render_template('404.html'), 404

        db.session.commit()
        app.logger.info("Lesson updated successfully")
        flash('Lesson updated successfully!', 'success')
        return redirect(url_for('teacher_dashboard'))
    else:
        app.logger.error(f"Form validation failed: {form.errors}")
        app.logger.error(f"Form data: {form.data}")
        app.logger.error(f"CSRF token: {form.csrf_token.data}")
        flash('There was an error updating the lesson. Please check your input.', 'error')
        
    return render_template('teacher/editLesson.html', form=form, lesson=lesson)


# Student Only Routes!
@app.route('/student/dashboard')
@login_required
def student_dashboard():
    if session.get('user_type') != 'student':
        return redirect(url_for('index'))

    student = get_student_by_id(session['user_id'])
    if not student:
        app.logger.error(f"Student with ID {session['user_id']} not found.")
        return render_template('404.html'), 404
    
    user_timezone = get_user_timezone(student.timezone)
    most_recent_record = get_most_recent_lesson_record(student.id, 'student', student.timezone)
    upcoming_lessons = get_upcoming_lessons(student.id, 'student', student.timezone)

    cancel_lesson_form = CancelLessonForm()  # Define the cancel lesson form

    return render_template(
        'student/studentDashboard.html',
        profile=current_user.profile,
        most_recent_record=most_recent_record,
        upcoming_lessons=upcoming_lessons,
        cancel_lesson_form=cancel_lesson_form,  # Pass the cancel lesson form
        user_timezone=user_timezone  # Pass the timezone to the template
    )


@app.route('/cancelLesson/<int:lesson_id>', methods=['POST'])
@login_required
def cancel_lesson(lesson_id):
    form = CancelLessonForm()

    # Set lesson_id in the form's data
    form.lesson_id.data = lesson_id

    if form.validate_on_submit():
        success, message = cancel_student_lesson(lesson_id, current_user.id)
        flash(message, 'success' if success else 'error')
        return redirect(url_for('student_dashboard'))

    flash('Form submission error. Please try again.', 'error')
    return redirect(url_for('student_dashboard'))


@app.route('/student/lessonRecords')
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
            
    return render_template('student/lessonRecords.html', lesson_records=lesson_records, user_timezone=user_timezone)


@app.route('/student/editStudentProfile', methods=['GET', 'POST'])
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
    return render_template('student/editStudentProfile.html', form=form, profile=current_user.profile, profile_updated=profile_updated)


@app.route('/student/bookLesson', methods=['GET', 'POST'])
@login_required
def student_book_lesson():
    form = StudentLessonSlotForm()
    
    student = db.session.get(Student, current_user.id)
    if student is None:
        app.logger.error(f"Student with ID {current_user.id} not found.")
        return render_template('404.html'), 404
    
    user_timezone = get_user_timezone(student.timezone)
    week_offset = int(request.args.get('week_offset', 0))
    start_of_week_utc, end_of_week_utc = get_week_boundaries(student.timezone, week_offset)

    if request.method == 'POST':
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
        teacher_id_str = request.args.get('teacher_id')
        teacher_id = int(teacher_id_str) if teacher_id_str is not None else None
        available_slots = fetch_available_slots(student, start_of_week_utc, end_of_week_utc, teacher_id)
        available_slots_dict = convert_slots_to_dict(available_slots)
        session['available_slots'] = available_slots_dict

    for slot in available_slots:
        slot.start_time = ensure_timezone_aware(slot.start_time, student.timezone)
        slot.end_time = ensure_timezone_aware(slot.end_time, student.timezone)
        
    current_time = datetime.now(user_timezone)
    
    form.lesson_slot.choices = [
        (slot.id, f"{slot.start_time.strftime('%Y-%m-%d %I:%M %p')} - {slot.end_time.strftime('%I:%M %p')} with {slot.teacher.username}")
        for slot in available_slots
    ]

    available_teacher_ids = {slot.teacher.id for slot in available_slots}
    available_teachers = [teacher for teacher in Teacher.query.all() if teacher.id in available_teacher_ids]
    form.teacher.choices = [(teacher.id, teacher.username) for teacher in available_teachers]

    if request.method == 'POST' and form.validate_on_submit():
        lesson_record, error_message = update_student_booking(session, form, student, current_time)
        if error_message:
            print(error_message)
            return render_template(
                'student/bookLesson.html', 
                form=form, 
                available_slots=available_slots, 
                available_teachers=available_teachers,
                week_offset=week_offset, 
                remaining_lessons=student.remaining_lessons, 
                start_of_week=start_of_week_utc, 
                end_of_week=end_of_week_utc)

        print('Lesson booked successfully')
        return redirect(url_for('student_book_lesson', week_offset=week_offset))

    return render_template(
        'student/bookLesson.html', 
        form=form, 
        available_slots=available_slots, 
        available_teachers=available_teachers, 
        week_offset=week_offset, 
        remaining_lessons=student.remaining_lessons, 
        start_of_week=start_of_week_utc, 
        end_of_week=end_of_week_utc)

@app.route('/getSlots/<int:teacher_id>', methods=['GET'])
def get_slots(teacher_id):
    # Check if the student is logged in
    if 'user_id' not in session:
        return jsonify({'error': 'Not logged in'}), 401

    # Get the student's timezone
    student = db.session.get(Student, session['user_id'])
    if student is None:
        return jsonify({'error': 'Student not found'}), 404

    start_of_week, end_of_week = get_week_boundaries(student.timezone)
    user_timezone = get_user_timezone(student.timezone)
    slots_dict = fetch_and_format_slots(student, teacher_id, start_of_week, end_of_week, user_timezone)

    return jsonify(slots_dict)



@app.teardown_appcontext
def shutdown_session(exception=None):
    db.session.remove()


if __name__ == '__main__':
    app.run(debug=True)