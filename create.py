import os

# Dictionary mapping file paths to their content
files = {
    # Main application factory
    "app.py": """\
from flask import Flask, render_template
from blueprints.odoo import odoo_bp
from blueprints.procfy import procfy_bp

def create_app():
    app = Flask(__name__)
    app.config.from_object('config.Config')

    # Register blueprints
    app.register_blueprint(odoo_bp, url_prefix='/odoo')
    app.register_blueprint(procfy_bp, url_prefix='/procfy')

    # Home route with card-based homepage
    @app.route('/')
    def home():
        return render_template('index.html')

    return app

if __name__ == '__main__':
    app = create_app()
    app.run(debug=True)
""",
    # Configuration file
    "config.py": """\
class Config:
    SECRET_KEY = 'your_secret_key'
    DEBUG = True
""",
    # Requirements
    "requirements.txt": """\
Flask
openpyxl
""",
    # Blueprints base __init__.py
    "blueprints/__init__.py": "",
    # Odoo blueprint __init__.py
    "blueprints/odoo/__init__.py": """\
from flask import Blueprint

odoo_bp = Blueprint('odoo', __name__, template_folder='templates')

from . import views, handlers
""",
    # Odoo handlers (combining your odoo scripts)
    "blueprints/odoo/handlers.py": """\
import xmlrpc.client
import csv
import os
import base64

# Odoo Configuration
URL = "https://mmg-locacao.odoo.com"
DB = "mmg-locacao"
USERNAME = "guiborel@hotmail.com"
PASSWORD = "Arseniu1!"

common = xmlrpc.client.ServerProxy(f"{URL}/xmlrpc/2/common")
uid = common.authenticate(DB, USERNAME, PASSWORD, {})
models = xmlrpc.client.ServerProxy(f"{URL}/xmlrpc/2/object")

def list_odoo_models():
    if uid:
        model_names = models.execute_kw(DB, uid, PASSWORD, 'ir.model', 'search_read', [[]], {'fields': ['model', 'name']})
        result = "Available Odoo Models:\\n"
        for m in model_names:
            result += f"{m['name']} -> {m['model']}\\n"
        return result
    else:
        return "Authentication failed."

def clean_record(record):
    cleaned = {}
    for key, value in record.items():
        key = str(key)
        if isinstance(value, tuple) and len(value) > 1:
            cleaned[key] = value[1] if isinstance(value[1], str) else value[0]
        elif isinstance(value, list):
            cleaned[key] = ", ".join(map(str, value)) if value else ""
        elif isinstance(value, dict):
            cleaned[key] = str(value)
        else:
            cleaned[key] = value
    return cleaned

def fetch_invoices_fields():
    if not uid:
        return "Authentication failed."

    fields = [
        "sequence_prefix", "sequence_number", "message_main_attachment_id",
        "access_url", "name", "date", "state", "move_type", "is_storno",
        "journal_id", "company_id", "invoice_date", "invoice_date_due",
        "invoice_payment_term_id", "partner_id", "commercial_partner_id",
        "partner_shipping_id", "payment_state", "invoice_partner_display_name",
        "create_date"
    ]
    domain = [
        ("invoice_date", ">=", "2025-02-01"),
        ("invoice_date", "<=", "2025-02-28"),
        ("move_type", "=", "out_invoice")
    ]
    try:
        records = models.execute_kw(DB, uid, PASSWORD, "account.move", "search_read", [domain], {"fields": fields})
        if records:
            cleaned_records = [clean_record(rec) for rec in records]
            filename = "faturas_fevereiro_2025_selected_fields.csv"
            with open(filename, mode='w', newline='', encoding='utf-8') as file:
                writer = csv.DictWriter(file, fieldnames=fields, extrasaction='ignore')
                writer.writeheader()
                for rec in cleaned_records:
                    writer.writerow(rec)
            return f"Data exported to {filename}"
        else:
            return "No invoices found for February 2025."
    except Exception as e:
        return f"Error fetching invoices: {e}"

def query_table_data(model_name, export_csv=False):
    if not uid:
        return "Authentication failed."
    try:
        # Fetch all fields if none are specified
        fields_data = models.execute_kw(DB, uid, PASSWORD, model_name, 'fields_get', [], {'attributes': ['string']})
        fields = list(fields_data.keys())
        records = models.execute_kw(DB, uid, PASSWORD, model_name, 'search_read', [[]], {'fields': fields, 'limit': 10 if not export_csv else False})
        records = [{str(k): v for k, v in rec.items()} for rec in records]
        if records:
            if export_csv:
                filename = f"{model_name}.csv"
                with open(filename, mode='w', newline='', encoding='utf-8') as file:
                    writer = csv.DictWriter(file, fieldnames=fields)
                    writer.writeheader()
                    for rec in records:
                        for field in fields:
                            if field not in rec:
                                rec[field] = None
                        writer.writerow(rec)
                return f"Data exported to {filename}"
            else:
                return str(records)
        else:
            return f"No data found in {model_name}."
    except Exception as e:
        return f"Error fetching data from {model_name}: {e}"

def download_invoice_attachments():
    if not uid:
        return "Authentication failed."
    fields = ["name", "invoice_date", "message_main_attachment_id"]
    domain = [
        ("invoice_date", ">=", "2025-02-01"),
        ("invoice_date", "<=", "2025-02-28"),
        ("move_type", "=", "out_invoice")
    ]
    try:
        invoices = models.execute_kw(DB, uid, PASSWORD, "account.move", "search_read", [domain], {"fields": fields})
        if not invoices:
            return "No invoices found for February 2025."
        DOWNLOAD_FOLDER = "nota_fiscal"
        os.makedirs(DOWNLOAD_FOLDER, exist_ok=True)
        messages = []
        for inv in invoices:
            invoice_name = inv.get("name")
            attach_info = inv.get("message_main_attachment_id")
            if attach_info and isinstance(attach_info, list) and len(attach_info) == 2:
                attachment_id = attach_info[0]
                suggested_filename = attach_info[1]
                attachment_data = models.execute_kw(DB, uid, PASSWORD, "ir.attachment", "read", [[attachment_id]], {"fields": ["datas", "name"]})
                if attachment_data:
                    datas = attachment_data[0].get("datas")
                    attachment_name = attachment_data[0].get("name", suggested_filename)
                    if datas:
                        file_content = base64.b64decode(datas)
                        final_filename = attachment_name or suggested_filename
                        file_path = os.path.join(DOWNLOAD_FOLDER, final_filename)
                        with open(file_path, "wb") as f:
                            f.write(file_content)
                        messages.append(f"Downloaded attachment for invoice {invoice_name}: {file_path}")
                    else:
                        messages.append(f"No data found for attachment ID {attachment_id}.")
                else:
                    messages.append(f"No attachment record found for ID {attachment_id}.")
            else:
                messages.append(f"No main attachment found for invoice {invoice_name}.")
        return "\\n".join(messages)
    except Exception as e:
        return f"Error downloading attachments: {e}"
""",
    # Odoo views (exposing endpoints)
    "blueprints/odoo/views.py": """\
from flask import render_template, request
from . import odoo_bp
from .handlers import list_odoo_models, fetch_invoices_fields, query_table_data, download_invoice_attachments

@odoo_bp.route('/models')
def models_view():
    result = list_odoo_models()
    return render_template('odoo/models.html', result=result)

@odoo_bp.route('/invoices')
def invoices_view():
    result = fetch_invoices_fields()
    return render_template('odoo/invoices.html', result=result)

@odoo_bp.route('/query', methods=['GET', 'POST'])
def query_view():
    result = ""
    if request.method == 'POST':
        model_name = request.form.get('model_name')
        export_csv = request.form.get('export_csv') == 'on'
        result = query_table_data(model_name, export_csv)
    return render_template('odoo/query.html', result=result)

@odoo_bp.route('/download_receipts')
def download_receipts_view():
    result = download_invoice_attachments()
    return render_template('odoo/download.html', result=result)
""",
    # Procfy blueprint __init__.py
    "blueprints/procfy/__init__.py": """\
from flask import Blueprint

procfy_bp = Blueprint('procfy', __name__, template_folder='templates')

from . import views, handlers
""",
    # Procfy handlers (wrapping the Excel processing code)
    "blueprints/procfy/handlers.py": """\
import openpyxl

def process_excel_data():
    try:
        workbook = openpyxl.load_workbook("modelo_importacao_procfy.xlsx")
        sheet = workbook.active
        # Read header from first row
        cabecalho = [cell.value for cell in sheet[1]]
        # Default values to fill
        valores_padrao = {
            "Tipo de Lançamento": "Recebimentos",
            "Data de competência": "01/02/2025",
            "Descrição": "INV/",
            "Categoria": "Locação de equipamentos",
            "Recebido de/Pago a": "Cliente",
            "Pago?": "Não",
            "Modo de pagamento": "PIX"
        }
        # Map column names to their indices
        indices_colunas = {header: idx+1 for idx, header in enumerate(cabecalho)}
        for coluna, valor in valores_padrao.items():
            if coluna in indices_colunas:
                col_idx = indices_colunas[coluna]
                sheet.cell(row=2, column=col_idx).value = valor
        workbook.save("modelo_importacao_procfy_preenchido.xlsx")
        return "Excel processed and saved as 'modelo_importacao_procfy_preenchido.xlsx'."
    except Exception as e:
        return f"Error processing Excel: {e}"
""",
    # Procfy views
    "blueprints/procfy/views.py": """\
from flask import render_template, request
from . import procfy_bp
from .handlers import process_excel_data

@procfy_bp.route('/excel', methods=['GET', 'POST'])
def excel_view():
    result = ""
    if request.method == 'POST':
        result = process_excel_data()
    return render_template('procfy/excel.html', result=result)
""",
    # Base HTML template
    "templates/base.html": """\
<!doctype html>
<html lang="en">
  <head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>{% block title %}Receipt and Sales Organizer{% endblock %}</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <link rel="stylesheet" href="{{ url_for('static', filename='css/style.css') }}">
  </head>
  <body>
    <nav class="navbar navbar-expand-lg navbar-dark bg-dark">
      <div class="container">
        <a class="navbar-brand" href="{{ url_for('home') }}">Organizer</a>
        <div class="collapse navbar-collapse">
          <ul class="navbar-nav me-auto">
            <li class="nav-item"><a class="nav-link" href="{{ url_for('odoo.models_view') }}">Odoo Models</a></li>
            <li class="nav-item"><a class="nav-link" href="{{ url_for('odoo.invoices_view') }}">Odoo Invoices</a></li>
            <li class="nav-item"><a class="nav-link" href="{{ url_for('odoo.query_view') }}">Odoo Query</a></li>
            <li class="nav-item"><a class="nav-link" href="{{ url_for('odoo.download_receipts_view') }}">Download Receipts</a></li>
            <li class="nav-item"><a class="nav-link" href="{{ url_for('procfy.excel_view') }}">Process Excel</a></li>
          </ul>
        </div>
      </div>
    </nav>
    <div class="container my-5">
      {% block content %}{% endblock %}
    </div>
    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script>
  </body>
</html>
""",
    # Home page with cards
    "templates/index.html": """\
{% extends 'base.html' %}
{% block title %}Home - Receipt and Sales Organizer{% endblock %}
{% block content %}
<div class="row">
  <div class="col-md-4">
    <div class="card mb-4 shadow-sm">
      <div class="card-body">
        <h5 class="card-title">Odoo Models</h5>
        <p class="card-text">List available Odoo models.</p>
        <a href="{{ url_for('odoo.models_view') }}" class="btn btn-primary">Go</a>
      </div>
    </div>
  </div>
  <div class="col-md-4">
    <div class="card mb-4 shadow-sm">
      <div class="card-body">
        <h5 class="card-title">Odoo Invoices</h5>
        <p class="card-text">Fetch invoices for February 2025.</p>
        <a href="{{ url_for('odoo.invoices_view') }}" class="btn btn-primary">Go</a>
      </div>
    </div>
  </div>
  <div class="col-md-4">
    <div class="card mb-4 shadow-sm">
      <div class="card-body">
        <h5 class="card-title">Odoo Query</h5>
        <p class="card-text">Query any Odoo model data.</p>
        <a href="{{ url_for('odoo.query_view') }}" class="btn btn-primary">Go</a>
      </div>
    </div>
  </div>
  <div class="col-md-4">
    <div class="card mb-4 shadow-sm">
      <div class="card-body">
        <h5 class="card-title">Download Receipts</h5>
        <p class="card-text">Download invoice attachments.</p>
        <a href="{{ url_for('odoo.download_receipts_view') }}" class="btn btn-primary">Go</a>
      </div>
    </div>
  </div>
  <div class="col-md-4">
    <div class="card mb-4 shadow-sm">
      <div class="card-body">
        <h5 class="card-title">Process Excel Data</h5>
        <p class="card-text">Process Procfy Excel data.</p>
        <a href="{{ url_for('procfy.excel_view') }}" class="btn btn-primary">Go</a>
      </div>
    </div>
  </div>
</div>
{% endblock %}
""",
    # Odoo Models template
    "templates/odoo/models.html": """\
{% extends 'base.html' %}
{% block title %}Odoo Models{% endblock %}
{% block content %}
<h2>Odoo Models</h2>
<pre>{{ result }}</pre>
{% endblock %}
""",
    # Odoo Invoices template
    "templates/odoo/invoices.html": """\
{% extends 'base.html' %}
{% block title %}Odoo Invoices{% endblock %}
{% block content %}
<h2>Odoo Invoices (February 2025)</h2>
<pre>{{ result }}</pre>
{% endblock %}
""",
    # Odoo Query template
    "templates/odoo/query.html": """\
{% extends 'base.html' %}
{% block title %}Odoo Query{% endblock %}
{% block content %}
<h2>Odoo Query</h2>
<form method="post">
  <div class="mb-3">
    <label for="model_name" class="form-label">Model Name</label>
    <input type="text" class="form-control" id="model_name" name="model_name" placeholder="e.g., res.partner" required>
  </div>
  <div class="form-check mb-3">
    <input type="checkbox" class="form-check-input" id="export_csv" name="export_csv">
    <label class="form-check-label" for="export_csv">Export to CSV</label>
  </div>
  <button type="submit" class="btn btn-primary">Query</button>
</form>
<pre>{{ result }}</pre>
{% endblock %}
""",
    # Odoo Download Receipts template
    "templates/odoo/download.html": """\
{% extends 'base.html' %}
{% block title %}Download Receipts{% endblock %}
{% block content %}
<h2>Download Invoice Attachments</h2>
<pre>{{ result }}</pre>
{% endblock %}
""",
    # Procfy Excel template
    "templates/procfy/excel.html": """\
{% extends 'base.html' %}
{% block title %}Process Excel Data{% endblock %}
{% block content %}
<h2>Process Procfy Excel Data</h2>
<form method="post">
  <button type="submit" class="btn btn-primary">Process Excel</button>
</form>
<pre>{{ result }}</pre>
{% endblock %}
""",
    # Static CSS
    "static/css/style.css": """\
/* Custom styles */
body {
  padding-top: 60px;
}
"""
}

# Create each file (and directory) if it does not exist
for filepath, content in files.items():
    directory = os.path.dirname(filepath)
    if directory and not os.path.exists(directory):
        os.makedirs(directory, exist_ok=True)
        print(f"Created directory: {directory}")
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(content)
        print(f"Created file: {filepath}")

print("Modular Flask project structure has been created!")
