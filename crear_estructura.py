import os
from datetime import date
import pandas as pd

BASE_DIR = "data"
folders = [
    "catalogo",
    "recetas",
    "entradas",
    "transferencias",
    "ventas_procesadas",
    "auditorias/apertura",
    "auditorias/cierre",
    "cierres_confirmados",
    "plantillas",
]

hoy = date.today().isoformat()

for folder in folders:
    os.makedirs(os.path.join(BASE_DIR, folder), exist_ok=True)
print("✅ Carpetas creadas.")

# Crear archivos vacíos de Excel si no existen
catalogo_file = os.path.join(BASE_DIR, "catalogo", f"catalogo_{hoy}.xlsx")
if not os.path.exists(catalogo_file):
    pd.DataFrame(
        columns=["Item", "Subcategoría", "Tipo de unidad", "Cantidad por unidad"]
    ).to_excel(catalogo_file, index=False)
    print(f"✅ {catalogo_file} generado.")

recetas_file = os.path.join(BASE_DIR, "recetas", f"recetas_{hoy}.xlsx")
if not os.path.exists(recetas_file):
    with pd.ExcelWriter(recetas_file) as writer:
        pd.DataFrame(
            columns=["Producto vendido", "Item usado", "Subcategoría", "Cantidad usada"]
        ).to_excel(writer, sheet_name="Recetas", index=False)
        pd.DataFrame(
            columns=["Categoría", "Subcategoría", "Tipo de unidad", "Cantidad estándar usada"]
        ).to_excel(writer, sheet_name="ReglasEst", index=False)
    print(f"✅ {recetas_file} generado.")

plantilla_file = os.path.join(BASE_DIR, "plantillas", f"formato_conteo_{hoy}.xlsx")
if not os.path.exists(plantilla_file):
    pd.DataFrame(
        columns=[
            "Fecha",
            "Item",
            "Subcategoría",
            "Ubicación",
            "Conteo Apertura",
            "Requisicion",
            "Conteo Cierre",
            "Observaciones",
        ]
    ).to_excel(plantilla_file, index=False)
    print(f"✅ {plantilla_file} generado.")

print("🚀 Estructura terminada, ¡puedes empezar a usar la app!")
