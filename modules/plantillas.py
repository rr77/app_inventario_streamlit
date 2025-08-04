import streamlit as st
import pandas as pd
import os
from datetime import datetime

CATALOGO_PATH = "catalogo/catalogo.xlsx"
PLANTILLAS_FOLDER = "plantillas/"

def generar_plantilla_catalogo():
    """
    Genera DataFrame plantilla usando el catálogo vigente,
    una fila por item-ubicación.
    """
    if not os.path.exists(CATALOGO_PATH):
        st.error("¡No se encontró el archivo de catálogo!")
        return pd.DataFrame()
    cat = pd.read_excel(CATALOGO_PATH)
    ubicaciones = ["Almacén", "Barra", "Vinera"]
    filas = []
    for idx, row in cat.iterrows():
        for u in ubicaciones:
            filas.append({
                "Fecha": "",
                "Item": row["Item"],
                "Subcategoría": row["Subcategoría"],
                "Ubicación": u,
                "Conteo Apertura": "",
                "Requisicion": "",
                "Conteo Cierre": "",
                "Observaciones": ""
            })
    df = pd.DataFrame(filas)
    return df

def plantilla_module():
    st.title("Descargar Plantilla Oficial de Conteo Físico")
    st.info("""
        Descarga la plantilla oficial de conteo físico de stock.
        Utiliza esta hoja para registrar auditorías (apertura/cierre). Incluye el campo "Requisicion" para registrar solicitudes internas del día.
    """)
    df_plantilla = generar_plantilla_catalogo()
    if df_plantilla.empty:
        st.warning("No se pudo generar la plantilla. ¿El catálogo está cargado?")
        return

    nombre_archivo = f"plantilla_conteo_{datetime.today().strftime('%Y-%m-%d')}.xlsx"
    ruta = os.path.join(PLANTILLAS_FOLDER, nombre_archivo)

    # Guardar por si acaso, aunque la app permite descargar directo
    df_plantilla.to_excel(ruta, index=False)

    st.dataframe(df_plantilla.head(12))
    st.download_button(
        label="Descargar plantilla Excel",
        data=df_plantilla.to_excel(index=False, engine='xlsxwriter'),
        file_name=nombre_archivo,
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
    st.info("""
        **Columnas de la plantilla:**
        - Fecha
        - Item
        - Subcategoría
        - Ubicación (Almacén, Barra o Vinera)
        - Conteo Apertura
        - Requisicion (pedido del día desde Almacén)
        - Conteo Cierre
        - Observaciones
    """)
    