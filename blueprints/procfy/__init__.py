# blueprints/procfy/__init__.py
from flask import Blueprint

procfy = Blueprint('procfy', __name__, template_folder='templates')

from . import views, handlers