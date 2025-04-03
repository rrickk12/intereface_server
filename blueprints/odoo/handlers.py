import xmlrpc.client
import csv
import os
import base64
import zipfile

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
        result = "Available Odoo Models:\n"
        for m in model_names:
            result += f"{m['name']} -> {m['model']}\n"
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

def fetch_invoices_fields_date_range(start_date, end_date):
    if not uid:
        return "Authentication failed."

    fields = [
        "sequence_prefix",
        "sequence_number",
        "message_main_attachment_id",
        "access_url",
        "name",
        "date",
        "state",
        "move_type",
        "is_storno",
        "journal_id",
        "company_id",
        "invoice_date",
        "invoice_date_due",
        "invoice_payment_term_id",
        "partner_id",
        "commercial_partner_id",
        "partner_shipping_id",
        "payment_state",
        "invoice_partner_display_name",
        "create_date",
        "amount_total"
    ]
    domain = [
        ("invoice_date", ">=", start_date),
        ("invoice_date", "<=", end_date),
        ("move_type", "=", "out_invoice")
    ]
    try:
        records = models.execute_kw(DB, uid, PASSWORD, "account.move", "search_read", [domain], {"fields": fields})
        if records:
            cleaned_records = [clean_record(rec) for rec in records]
            # Save file in a public folder (static/downloads)
            output_dir = os.path.join("static", "downloads")
            os.makedirs(output_dir, exist_ok=True)
            filename = os.path.join(output_dir, f"faturas_{start_date}_{end_date}_selected_fields.csv")
            with open(filename, mode='w', newline='', encoding='utf-8') as file:
                writer = csv.DictWriter(file, fieldnames=fields, extrasaction='ignore')
                writer.writeheader()
                for rec in cleaned_records:
                    writer.writerow(rec)
            # Return a link for the user to download the generated file.
            return f"Data exported to <a href='/odoo/download_file?file={os.path.basename(filename)}'> {os.path.basename(filename)} </a>"
        else:
            return "No invoices found for the selected period."
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
                # Optionally store exported CSV in a public folder too.
                output_dir = os.path.join("static", "downloads")
                os.makedirs(output_dir, exist_ok=True)
                filename = os.path.join(output_dir, f"{model_name}.csv")
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

def download_invoice_attachments(start_date, end_date, zip_archive=False):
    if not uid:
        return {"error": "Authentication failed."}

    fields = ["name", "invoice_date", "message_main_attachment_id"]
    domain = [
        ("invoice_date", ">=", start_date),
        ("invoice_date", "<=", end_date),
        ("move_type", "=", "out_invoice")
    ]
    try:
        invoices = models.execute_kw(DB, uid, PASSWORD, "account.move", "search_read", [domain], {"fields": fields})
        if not invoices:
            return {"messages": f"No invoices found for the period {start_date} to {end_date}."}

        # Save attachments in a public folder (static/nota_fiscal)
        DOWNLOAD_FOLDER = os.path.join("static", "nota_fiscal")
        os.makedirs(DOWNLOAD_FOLDER, exist_ok=True)
        messages = []
        downloaded_files = []  # Keep track of downloaded file paths

        for inv in invoices:
            invoice_name = inv.get("name")
            attach_info = inv.get("message_main_attachment_id")
            if attach_info and isinstance(attach_info, list) and len(attach_info) == 2:
                attachment_id = attach_info[0]
                suggested_filename = attach_info[1]
                attachment_data = models.execute_kw(
                    DB, uid, PASSWORD, "ir.attachment", "read",
                    [[attachment_id]], {"fields": ["datas", "name"]}
                )
                if attachment_data:
                    datas = attachment_data[0].get("datas")
                    attachment_name = attachment_data[0].get("name", suggested_filename)
                    if datas:
                        file_content = base64.b64decode(datas)
                        final_filename = attachment_name or suggested_filename
                        file_path = os.path.join(DOWNLOAD_FOLDER, final_filename)
                        with open(file_path, "wb") as f:
                            f.write(file_content)
                        downloaded_files.append(file_path)
                        messages.append(f"Downloaded attachment for invoice {invoice_name}: {file_path}")
                    else:
                        messages.append(f"No data found for attachment ID {attachment_id}.")
                else:
                    messages.append(f"No attachment record found for ID {attachment_id}.")
            else:
                messages.append(f"No main attachment found for invoice {invoice_name}.")

        result = {"messages": "\n".join(messages)}

        # If ZIP is requested
        if zip_archive and downloaded_files:
            zip_filename = os.path.join(DOWNLOAD_FOLDER, f"receipts_{start_date}_{end_date}.zip")
            with zipfile.ZipFile(zip_filename, 'w') as zipf:
                for file_path in downloaded_files:
                    zipf.write(file_path, arcname=os.path.basename(file_path))
            result["zip_file"] = os.path.basename(zip_filename)
            result["messages"] += f"\nZip archive created: {os.path.basename(zip_filename)}"

        # If individual files only
        elif not zip_archive and downloaded_files:
            result["files"] = [os.path.basename(path) for path in downloaded_files]

        return result
    except Exception as e:
        return {"error": f"Error downloading attachments: {e}"}
