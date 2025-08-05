import streamlit as st
import pandas as pd
import os
from utils.excel_tools import to_excel_bytes_multiple_sheets
from utils.path_utils import RECETAS_DIR, latest_file

def load_recetas():
    """
    Carga las hojas de Recetas y Reglas Estándar desde el archivo más reciente
    ubicado en `data/recetas/`. Si no existen, devuelve DataFrames vacíos con
    las columnas correctas.
    """
    path = latest_file(RECETAS_DIR, "recetas")
    if path and os.path.exists(path):
        try:
            xls = pd.ExcelFile(path)
            # Espera dos hojas exactas: 'Recetas' y 'ReglasEst'
            df_recetas = pd.read_excel(xls, "Recetas")
            df_reglas = pd.read_excel(xls, "ReglasEst")
        except Exception as e:
            st.error(f"Error cargando recetas.xlsx: {str(e)}")
            df_recetas = pd.DataFrame(columns=["Producto vendido", "Item usado", "Subcategoría", "Cantidad usada"])
            df_reglas = pd.DataFrame(columns=["Categoría", "Subcategoría", "Tipo de unidad", "Cantidad estándar usada"])
    else:
        df_recetas = pd.DataFrame(columns=["Producto vendido", "Item usado", "Subcategoría", "Cantidad usada"])
        df_reglas = pd.DataFrame(columns=["Categoría", "Subcategoría", "Tipo de unidad", "Cantidad estándar usada"])
    return df_recetas, df_reglas

def recetas_module():
    st.title("Recetas (Consumo Teórico)")

    st.info("""
    Este módulo muestra las recetas de productos y las reglas estándar de consumo.
    - La edición/mantenimiento SOLO se realiza en el archivo más reciente dentro de `data/recetas/` (dos hojas: Recetas y ReglasEst).
    - Las recetas determinan el consumo teórico de inventario a partir de las ventas.
    """)

    df_recetas, df_reglas = load_recetas()

    st.subheader("Recetas de Productos (por venta)")
    st.dataframe(df_recetas)

    st.markdown("---")
    st.subheader("Reglas Estándar (consumo genérico por subcategoría)")
    st.dataframe(df_reglas)

    # Exportar ambas hojas unificadas, SOLO EN MEMORIA
    st.download_button(
        label="Descargar archivo de recetas (Excel)",
        data=to_excel_bytes_multiple_sheets({"Recetas": df_recetas, "ReglasEst": df_reglas}),
        file_name="recetas.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )