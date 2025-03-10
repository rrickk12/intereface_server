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
