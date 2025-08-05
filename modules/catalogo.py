import streamlit as st
import pandas as pd
import os
from utils.excel_tools import to_excel_bytes
from utils.path_utils import CATALOGO_DIR, latest_file


EXPECTED_COLUMNS = [
    "Item",
    "Subcategoría",
    "Tipo_venta",
    "Unidad",
    "Volumen_ml_por_unidad",
    "Dosis_ml",
]


def load_catalog():
    """Carga y valida el catálogo de productos desde Excel."""
    path = latest_file(CATALOGO_DIR, "catalogo")
    if path and os.path.exists(path):
        df = pd.read_excel(path)
        if "Item" not in df.columns and "Nombre" in df.columns:
            df = df.rename(columns={"Nombre": "Item"})
    else:
        # Si el catálogo no existe, retorna DataFrame vacío con columnas esperadas
        df = pd.DataFrame(columns=EXPECTED_COLUMNS)

    missing = [c for c in EXPECTED_COLUMNS if c not in df.columns]
    if missing:
        st.error(f"Catálogo incompleto. Faltan columnas: {', '.join(missing)}")
        df = df.reindex(columns=EXPECTED_COLUMNS)
    if "Nombre" not in df.columns and "Item" in df.columns:
        df["Nombre"] = df["Item"]

    # Validaciones específicas por tipo de venta
    if not df.empty:
        bot_missing = df[(df["Tipo_venta"] == "BOT") & df["Volumen_ml_por_unidad"].isna()]
        trg_missing = df[(df["Tipo_venta"] == "TRG") & df["Dosis_ml"].isna()]
        if not bot_missing.empty:
            st.warning(
                "Hay productos de tipo BOT sin 'Volumen_ml_por_unidad'. Verifica el catálogo."
            )
        if not trg_missing.empty:
            st.warning(
                "Hay productos de tipo TRG sin 'Dosis_ml'. Verifica el catálogo."
            )
    return df

def catalogo_module():
    st.title("Catálogo de Productos")
    st.info("""
    El catálogo de productos define todos los ítems únicos en inventario.
    ✏️ **La edición del catálogo se realiza desde Excel:**
    por favor edita el archivo más reciente en `data/catalogo/` manualmente fuera de la app.

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
        "- Item\n"
        "- Subcategoría\n"
        "- Tipo_venta (BOT, TRG, CTL)\n"
        "- Unidad (ml, botella, etc.)\n"
        "- Volumen_ml_por_unidad (si Tipo_venta = BOT)\n"
        "- Dosis_ml (si Tipo_venta = TRG)"
    )