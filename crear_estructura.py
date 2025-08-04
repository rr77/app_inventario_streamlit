import os
import pandas as pd

folders = [
    "catalogo",
    "recetas",
    "entradas",
    "transferencias",
    "ventas_procesadas",
    "auditorias/apertura",
    "auditorias/cierre",
    "cierres_confirmados",
    "plantillas"
]

for folder in folders:
    os.makedirs(folder, exist_ok=True)
print("✅ Carpetas creadas.")

# Crear archivos vacíos de Excel si no existen
if not os.path.exists("catalogo/catalogo.xlsx"):
    pd.DataFrame(columns=["Item", "Subcategoría", "Tipo de unidad", "Cantidad por unidad"]).to_excel("catalogo/catalogo.xlsx", index=False)
    print("✅ catalogo/catalogo.xlsx generado.")

if not os.path.exists("recetas/recetas.xlsx"):
    with pd.ExcelWriter("recetas/recetas.xlsx") as writer:
        pd.DataFrame(columns=["Producto vendido", "Item usado", "Subcategoría", "Cantidad usada"]).to_excel(writer, sheet_name="Recetas", index=False)
        pd.DataFrame(columns=["Categoría","Subcategoría","Tipo de unidad","Cantidad estándar usada"]).to_excel(writer, sheet_name="ReglasEst", index=False)
    print("✅ recetas/recetas.xlsx generado.")

if not os.path.exists("plantillas/formato_conteo.xlsx"):
    pd.DataFrame(columns=["Fecha","Item","Subcategoría","Ubicación","Conteo Apertura","Requisicion","Conteo Cierre","Observaciones"]).to_excel("plantillas/formato_conteo.xlsx", index=False)
    print("✅ plantillas/formato_conteo.xlsx generado.")

print("🚀 Estructura terminada, ¡puedes empezar a usar la app!")