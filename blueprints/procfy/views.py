from flask import Blueprint, render_template, request, send_from_directory
import os
from .handlers import fill_procfy_template

procfy = Blueprint('procfy', __name__, template_folder='templates')

@procfy.route('/excel', methods=['GET', 'POST'])
def excel_view():
    result = ""
    if request.method == 'POST':
        file = request.files.get('odoo_csv')
        # Captura o valor do seletor de conta
        conta_selecionada = request.form.get('account_selector', 'Sicoob 2')
        if file:
            csv_path = os.path.join('static', 'downloads', 'temp_odoo.csv')
            file.save(csv_path)
            procfy_template = "modelo_Procfy_MMG.xlsx"
            output_xlsx = os.path.join('static', 'downloads', 'procfy_preenchido.xlsx')
            try:
                # Passa o parâmetro 'conta_selecionada' para a função
                fill_procfy_template(csv_path, procfy_template, output_xlsx, conta_selecionada)
                result = "Arquivo XLSX preenchido com sucesso. "
                result += f"<a href='/procfy/download/procfy_preenchido.xlsx'>Baixar XLSX</a>"
            except Exception as e:
                result = f"Erro ao processar: {str(e)}"
        else:
            result = "Nenhum arquivo CSV enviado."
    return render_template('procfy/excel.html', result=result)

@procfy.route('/download/<path:filename>')
def download_file(filename):
    return send_from_directory(os.path.join('static', 'downloads'), filename, as_attachment=True)
