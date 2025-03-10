from flask import Blueprint

odoo_bp = Blueprint('odoo', __name__, template_folder='templates')

from . import views, handlers
