from fpdf import FPDF
import pandas as pd

def create_pdf_from_csv(csv_path: str, pdf_path: str):
    df = pd.read_csv(csv_path)

    pdf = FPDF(orientation='L', unit='mm', format='A4')
    pdf.add_page()
    pdf.set_font("Helvetica", size=10)  

    # Заголовок
    pdf.cell(0, 10, "14-Day Weather Forecast for Wroclaw", ln=True, align="C")

    col_width = 40
    row_height = 8

    # Заголовки таблиці
    for header in df.columns:
        pdf.cell(col_width, row_height, str(header), border=1)
    pdf.ln(row_height)

    # Дані таблиці
    for _, row in df.iterrows():
        for item in row:
            pdf.cell(col_width, row_height, str(item), border=1)
        pdf.ln(row_height)

    pdf.output(pdf_path)
