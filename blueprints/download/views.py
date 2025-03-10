from flask import render_template
from . import download_bp

@download_bp.route('/')
def download_page():
    # Code for download functionality
    return render_template('download.html')
