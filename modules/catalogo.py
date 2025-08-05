import streamlit as st
import pandas as pd
import os
from utils.excel_tools import to_excel_bytes
from utils.paths import CATALOGO_PATH

def load_catalog():
    """Carga el catálogo de productos desde Excel."""
    if os.path.exists(CATALOGO_PATH):
        df = pd.read_excel(CATALOGO_PATH)
    else:
        # Si el catálogo no existe, retorna DataFrame vacío con columnas esperadas
        df = pd.DataFrame(columns=["Item", "Subcategoría", "Tipo de unidad", "Cantidad por unidad"])
    return df

def catalogo_module():
    st.title("Catálogo de Productos")
    st.info("""
    El catálogo de productos define todos los ítems únicos en inventario.
    ✏️ **La edición del catálogo se realiza desde Excel:**  
    por favor edita `catalogo/catalogo.xlsx` manualmente fuera de la app.

    Aquí puedes consultar y exportar el catálogo actual para uso operativo y validación.
    """)
    
    # Carga y muestra el catálogo
    df = load_catalog()
    st.dataframe(df)
    

    # Descarga del catálogo
    st.download_button(
        label="Descargar catálogo en Excel",
        data=to_excel_bytes(df),
        file_name="catalogo_producto.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

    st.info(
        "**Formato requerido:**\n"
        "- Item (nombre único)\n"
        "- Subcategoría (ej. Vodka, Ron, Whisky...)\n"
        "- Tipo de unidad (ml / unidad)\n"
        "- Cantidad por unidad (normalmente 750ml, 1l, 24 unidades, etc.)"
    )