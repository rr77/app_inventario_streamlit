from fpdf import FPDF
import pandas as pd
import os
from datetime import datetime
from utils.path_utils import REPORTES_PDF_DIR

LOGO_PATH = os.path.join(REPORTES_PDF_DIR, "logo.png")  # Cambia esto si tu logo está en otra ubicación

class PDF(FPDF):
    def header(self):
        # Logo (opcional)
        if os.path.exists(LOGO_PATH):
            self.image(LOGO_PATH, 10, 8, 20)
        self.set_font('Arial', 'B', 14)
        self.cell(0, 10, self.title, ln=1, align='C')
        self.ln(5)

    def footer(self):
        self.set_y(-15)
        self.set_font('Arial', 'I', 8)
        self.cell(0, 10, f'Página {self.page_no()} - {datetime.today().strftime("%Y-%m-%d %H:%M")}', 0, 0, 'C')

    def tabla(self, dataframe: pd.DataFrame):
        self.set_font("Arial", size=9)
        # Ancho de columna automático
        col_widths = []
        for col in dataframe.columns:
            max_content = max(dataframe[col].astype(str).apply(len).max(), len(str(col)))
            col_widths.append(max(18, min(40, max_content*4.2)))
        # Encabezado
        for i, col in enumerate(dataframe.columns):
            self.cell(col_widths[i], 8, str(col), 1, 0, "C", fill=True)
        self.ln()
        # Filas
        for idx, row in dataframe.iterrows():
            for i, col in enumerate(dataframe.columns):
                val = str(row[col])
                self.cell(col_widths[i], 8, val[:25], 1, 0, "C")
            self.ln()

def generar_pdf_apertura(df, ruta_pdf=None):
    pdf = PDF()
    pdf.title = "Auditoría de Apertura de Inventario"
    pdf.add_page()
    pdf.set_fill_color(220, 220, 220)
    pdf.set_font("Arial", "B", 11)
    pdf.cell(0, 10, f"Fecha: {datetime.today().strftime('%Y-%m-%d')}", ln=1)
    pdf.ln(2)
    pdf.tabla(df)
    pdf.ln(6)
    pdf.set_font("Arial", "I", 10)
    pdf.cell(0, 10, "Auditoría generada automáticamente por el sistema de inventario.", ln=1)
    pdf_bytes = pdf.output(dest="S").encode("latin-1")
    if ruta_pdf:
        with open(ruta_pdf, "wb") as f:
            f.write(pdf_bytes)
    return pdf_bytes

def generar_pdf_cierre(df, ruta_pdf=None):
    pdf = PDF()
    pdf.title = "Auditoría de Cierre de Inventario"
    pdf.add_page()
    pdf.set_fill_color(220, 220, 220)
    pdf.set_font("Arial", "B", 11)
    pdf.cell(0, 10, f"Fecha: {datetime.today().strftime('%Y-%m-%d')}", ln=1)
    # Resumen de diferencias
    pdf.set_font("Arial", "", 10)
    dif_total = round(df["Diferencia"].sum(), 2) if "Diferencia" in df else 0
    pdf.cell(0, 8, f"Total diferencia de stock (todas ubicaciones): {dif_total}", ln=1)
    pdf.ln(2)
    pdf.tabla(df)
    pdf.ln(6)
    pdf.set_font("Arial", "I", 10)
    pdf.cell(0, 10, "Auditoría generada automáticamente por el sistema de inventario.", ln=1)
    pdf_bytes = pdf.output(dest="S").encode("latin-1")
    if ruta_pdf:
        with open(ruta_pdf, "wb") as f:
            f.write(pdf_bytes)
    return pdf_bytes