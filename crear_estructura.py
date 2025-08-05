import os
import pandas as pd
from utils.paths import ensure_dirs, CATALOGO_PATH, RECETAS_PATH, PLANTILLAS_FOLDER

ensure_dirs()
print("✅ Carpetas creadas.")

# Crear archivos vacíos de Excel si no existen
if not os.path.exists(CATALOGO_PATH):
    pd.DataFrame(columns=["Item", "Subcategoría", "Tipo de unidad", "Cantidad por unidad"]).to_excel(CATALOGO_PATH, index=False)
    print("✅ catalogo/catalogo.xlsx generado.")

if not os.path.exists(RECETAS_PATH):
    with pd.ExcelWriter(RECETAS_PATH) as writer:
        pd.DataFrame(columns=["Producto vendido", "Item usado", "Subcategoría", "Cantidad usada"]).to_excel(writer, sheet_name="Recetas", index=False)
        pd.DataFrame(columns=["Categoría","Subcategoría","Tipo de unidad","Cantidad estándar usada"]).to_excel(writer, sheet_name="ReglasEst", index=False)
    print("✅ recetas/recetas.xlsx generado.")

formato_path = os.path.join(PLANTILLAS_FOLDER, "formato_conteo.xlsx")
if not os.path.exists(formato_path):
    pd.DataFrame(columns=["Fecha","Item","Subcategoría","Ubicación","Conteo Apertura","Requisicion","Conteo Cierre","Observaciones"]).to_excel(formato_path, index=False)
    print("✅ plantillas/formato_conteo.xlsx generado.")

print("🚀 Estructura terminada, ¡puedes empezar a usar la app!")