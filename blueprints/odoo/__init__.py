from flask import Blueprint

# Create the blueprint instance once
odoo_bp = Blueprint('odoo', __name__, template_folder='templates')

# Import routes that will use this blueprint
from . import views
