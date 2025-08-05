from fpdf import FPDF
import pandas as pd
import os
from datetime import datetime
from utils.path_utils import REPORTES_PDF_DIR

LOGO_PATH = os.path.join(REPORTES_PDF_DIR, "logo.png")  # Cambia esto si tu logo está en otra ubicación


def _safe_text(text) -> str:
    """Devuelve *text* convertido a latin-1, reemplazando caracteres no soportados.

    FPDF solo admite el conjunto de caracteres latin-1 para las fuentes básicas.
    Este helper evita errores de codificación reemplazando cualquier caracter que
    no pueda representarse.
    """

    return str(text).encode("latin-1", "replace").decode("latin-1")

class PDF(FPDF):
    def header(self):
        # Logo (opcional)
        if os.path.exists(LOGO_PATH):
            self.image(LOGO_PATH, 10, 8, 20)
        self.set_font('Arial', 'B', 14)
        self.cell(0, 10, _safe_text(self.title), ln=1, align='C')
        self.ln(5)

    def footer(self):
        self.set_y(-15)
        self.set_font('Arial', 'I', 8)
        footer_text = f'Página {self.page_no()} - {datetime.today().strftime("%Y-%m-%d %H:%M")}'
        self.cell(0, 10, _safe_text(footer_text), 0, 0, 'C')

    def tabla(self, dataframe: pd.DataFrame):
        self.set_font("Arial", size=9)
        # Ancho de columna automático
        col_widths = []
        for col in dataframe.columns:
            max_content = max(dataframe[col].astype(str).apply(len).max(), len(str(col)))
            col_widths.append(max(18, min(40, max_content*4.2)))
        # Encabezado
        for i, col in enumerate(dataframe.columns):
            self.cell(col_widths[i], 8, _safe_text(col), 1, 0, "C", fill=True)
        self.ln()
        # Filas
        for idx, row in dataframe.iterrows():
            for i, col in enumerate(dataframe.columns):
                val = _safe_text(row[col])
                self.cell(col_widths[i], 8, val[:25], 1, 0, "C")
            self.ln()

def generar_pdf_apertura(df, ruta_pdf=None):
    pdf = PDF()
    pdf.title = "Auditoría de Apertura de Inventario"
    pdf.add_page()
    pdf.set_fill_color(220, 220, 220)
    pdf.set_font("Arial", "B", 11)
    pdf.cell(0, 10, _safe_text(f"Fecha: {datetime.today().strftime('%Y-%m-%d')}"), ln=1)
    pdf.ln(2)
    pdf.tabla(df)
    pdf.ln(6)
    pdf.set_font("Arial", "I", 10)
    pdf.cell(0, 10, _safe_text("Auditoría generada automáticamente por el sistema de inventario."), ln=1)
    pdf_bytes = pdf.output(dest="S").encode("latin-1", "replace")
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
    pdf.cell(0, 10, _safe_text(f"Fecha: {datetime.today().strftime('%Y-%m-%d')}"), ln=1)
    # Resumen de diferencias
    pdf.set_font("Arial", "", 10)
    dif_total = round(df["Diferencia"].sum(), 2) if "Diferencia" in df else 0
    pdf.cell(0, 8, _safe_text(f"Total diferencia de stock (todas ubicaciones): {dif_total}"), ln=1)
    pdf.ln(2)
    pdf.tabla(df)
    pdf.ln(6)
    pdf.set_font("Arial", "I", 10)
    pdf.cell(0, 10, _safe_text("Auditoría generada automáticamente por el sistema de inventario."), ln=1)
    pdf_bytes = pdf.output(dest="S").encode("latin-1", "replace")
    if ruta_pdf:
        with open(ruta_pdf, "wb") as f:
            f.write(pdf_bytes)
    return pdf_bytes


def generar_pdf_stock(df, ruta_pdf=None):
    """Genera un reporte PDF genérico para el módulo de stock."""
    pdf = PDF()
    pdf.title = "Reporte de Stock Actual"
    pdf.add_page()
    pdf.set_fill_color(220, 220, 220)
    pdf.set_font("Arial", "B", 11)
    pdf.cell(0, 10, _safe_text(f"Fecha: {datetime.today().strftime('%Y-%m-%d')}"), ln=1)
    pdf.ln(2)
    pdf.tabla(df.round(2))
    pdf.ln(6)
    pdf.set_font("Arial", "I", 10)
    pdf.cell(0, 10, _safe_text("Reporte generado automáticamente por el sistema de inventario."), ln=1)
    pdf_bytes = pdf.output(dest="S").encode("latin-1", "replace")
    if ruta_pdf:
        with open(ruta_pdf, "wb") as f:
            f.write(pdf_bytes)
    return pdf_bytes
