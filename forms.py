from wtforms import ValidationError

class FileMaxSizeMB(object):
    def __init__(self, max_size_mb):
        self.max_size_mb = max_size_mb

    def __call__(self, form, field):
        file_size = len(field.data.read())
        field.data.seek(0)  # Reset file pointer to beginning
        if file_size > self.max_size_mb * 1024 * 1024:
            raise ValidationError(f'File size must be less than {self.max_size_mb}MB')