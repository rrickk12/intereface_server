from flask import render_template, request, redirect, url_for, flash
from . import upload_bp

@upload_bp.route('/', methods=['GET', 'POST'])
def upload_page():
    if request.method == 'POST':
        # Handle file upload here
        flash("File uploaded successfully!")
        return redirect(url_for('upload.upload_page'))
    return render_template('upload.html')
