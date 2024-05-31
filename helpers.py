import os
import secrets
from flask import current_app, session
from flask_login import current_user

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
