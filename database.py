"""
database.py

This module initializes the SQLAlchemy and Flask-Migrate extensions for use with the Flask application.
These extensions provide ORM capabilities and database migration support, respectively.
"""

from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate

# Initialize the SQLAlchemy extension
db = SQLAlchemy()

# Initialize the Flask-Migrate extension
migrate = Migrate()
