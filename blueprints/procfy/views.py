from flask import render_template, request
from . import procfy_bp
from .handlers import process_excel_data

@procfy_bp.route('/excel', methods=['GET', 'POST'])
def excel_view():
    result = ""
    if request.method == 'POST':
        result = process_excel_data()
    return render_template('procfy/excel.html', result=result)
