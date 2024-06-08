import os
import secrets
from flask import current_app, session
from flask_login import current_user

def save_image_file(image_file):
    """
    Save an uploaded image file with a unique name.
    The logic here was taken from ChatGPT, although I was able to implement and change aspects too!

    Generates a random filename for the uploaded image to ensure uniqueness,
    determines the appropriate directory based on the user type, and handles
    the saving and potential deletion of the old image file.

    Args:
        image_file (FileStorage): The uploaded image file.

    Returns:
        str: The new filename of the saved image.
    """
    # Generate a random hex for the filename to ensure it's unique
    random_hex = secrets.token_hex(8)
    _, file_extension = os.path.splitext(image_file.filename)
    new_filename = random_hex + file_extension

    # Determine the directory and default image based on the user type
    if session['user_type'] == 'teacher':
        directory = 'static/img/teacherImg'
        default_image = 'default.jpg'
    elif session['user_type'] == 'student':
        directory = 'static/img/studentImg'
        default_image = 'default1.jpg'
    else:
        return None  # Or handle this case differently

    # Build the full file path for the new image
    image_path = os.path.join(current_app.root_path, directory, new_filename)

    # Save the new image file
    image_file.save(image_path)

    # Only delete the old image if it's not the default image
    old_image_path = os.path.join(current_app.root_path, directory, current_user.profile.image_file)
    if current_user.profile.image_file != default_image and os.path.exists(old_image_path):
        try:
            os.remove(old_image_path)
        except PermissionError:
            pass  # Ignore the permission error

    return new_filename