from flask import render_template
from . import database_bp

@database_bp.route('/')
def database_page():
    # Code for database management functionality
    return render_template('database.html')
