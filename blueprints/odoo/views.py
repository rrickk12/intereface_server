from flask import render_template, request, jsonify,send_from_directory
from . import odoo_bp
from .handlers import list_odoo_models, fetch_invoices_fields_date_range, query_table_data, download_invoice_attachments

@odoo_bp.route('/models')
def models_view():
    result = list_odoo_models()
    return render_template('odoo/models.html', result=result)


@odoo_bp.route('/query', methods=['GET', 'POST'])
def query_view():
    result = ""
    if request.method == 'POST':
        model_name = request.form.get('model_name')
        export_csv = request.form.get('export_csv') == 'on'
        # Execute the query only after form submission.
        result = query_table_data(model_name, export_csv)
    return render_template('odoo/query.html', result=result)

@odoo_bp.route('/invoices', methods=['GET', 'POST'])
def invoices_date_range_view():
    result = ""
    if request.method == 'POST':
        start_date = request.form.get('start_date')
        end_date = request.form.get('end_date')
        result = fetch_invoices_fields_date_range(start_date, end_date)
    return render_template('odoo/invoices.html', result=result)


@odoo_bp.route('/download_receipts', methods=['GET', 'POST'])
def download_receipts_view():
    if request.method == 'POST':
        start_date = request.form.get('start_date')
        end_date = request.form.get('end_date')
        zip_archive = request.form.get('zip') == 'on'
        result = download_invoice_attachments(start_date, end_date, zip_archive)
        # Check for AJAX request using header.
        if request.headers.get("X-Requested-With") == "XMLHttpRequest":
            return jsonify(result=result)
        else:
            return render_template('odoo/download.html', result=result)
    return render_template('odoo/download.html', result={})

@odoo_bp.route('/download_file')
def download_file():
    file = request.args.get('file')
    if file:
        # Note: Ensure you are using the correct parameter name "path" for newer Flask versions.
        return send_from_directory(directory="nota_fiscal", path=file, as_attachment=True)
    return "File not found", 404