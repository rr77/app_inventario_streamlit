import os
from glob import glob

DATA_DIR = "data"
CATALOGO_DIR = os.path.join(DATA_DIR, "catalogo")
RECETAS_DIR = os.path.join(DATA_DIR, "recetas")
PLANTILLAS_DIR = os.path.join(DATA_DIR, "plantillas")
ENTRADAS_DIR = os.path.join(DATA_DIR, "entradas")
TRANSFERENCIAS_DIR = os.path.join(DATA_DIR, "transferencias")
VENTAS_PROCESADAS_DIR = os.path.join(DATA_DIR, "ventas_procesadas")
AUDITORIA_AP_DIR = os.path.join(DATA_DIR, "auditorias", "apertura")
AUDITORIA_CI_DIR = os.path.join(DATA_DIR, "auditorias", "cierre")
CIERRES_CONFIRMADOS_DIR = os.path.join(DATA_DIR, "cierres_confirmados")
REPORTES_PDF_DIR = os.path.join(DATA_DIR, "reportes_pdf")

def latest_file(folder, prefix):
    """Return the newest Excel file matching prefix_YYYY-MM-DD.xlsx in folder."""
    files = sorted(glob(os.path.join(folder, f"{prefix}_*.xlsx")))
    return files[-1] if files else None
