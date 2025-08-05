import os

# File paths
CATALOGO_PATH = "catalogo/catalogo.xlsx"
RECETAS_PATH = "recetas/recetas.xlsx"

# Folder paths
ENTRADAS_FOLDER = "entradas/"
TRANSFERENCIAS_FOLDER = "transferencias/"
VENTAS_PROCESADAS_FOLDER = "ventas_procesadas/"
AUDITORIA_AP_FOLDER = "auditorias/apertura/"
AUDITORIA_CI_FOLDER = "auditorias/cierre/"
CIERRES_CONFIRMADOS_FOLDER = "cierres_confirmados/"
PLANTILLAS_FOLDER = "plantillas/"
REPORTES_PDF_FOLDER = "reportes_pdf/"


def ensure_dirs() -> None:
    """Create required directories if they do not exist."""
    dirs = [
        os.path.dirname(CATALOGO_PATH),
        os.path.dirname(RECETAS_PATH),
        ENTRADAS_FOLDER,
        TRANSFERENCIAS_FOLDER,
        VENTAS_PROCESADAS_FOLDER,
        AUDITORIA_AP_FOLDER,
        AUDITORIA_CI_FOLDER,
        CIERRES_CONFIRMADOS_FOLDER,
        PLANTILLAS_FOLDER,
        REPORTES_PDF_FOLDER,
    ]
    for folder in dirs:
        if folder:
            os.makedirs(folder, exist_ok=True)
