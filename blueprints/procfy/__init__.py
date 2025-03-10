from flask import Blueprint

procfy_bp = Blueprint('procfy', __name__, template_folder='templates')

from . import views, handlers
