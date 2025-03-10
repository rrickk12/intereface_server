from flask import Blueprint

download_bp = Blueprint('download', __name__, template_folder='templates')

from . import views
