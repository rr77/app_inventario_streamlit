import os
import pandas as pd
import streamlit as st

from utils.excel_tools import to_excel_bytes
from utils.path_utils import RECETAS_DIR, latest_file
from modules.catalogo import load_catalog


EXPECTED_COLUMNS = [
    "Producto_vendido",
    "Ingrediente",
    "Unidad",
]


def load_recetas(catalogo: pd.DataFrame | None = None) -> pd.DataFrame:
    """Carga y valida la hoja de recetas."""
    path = latest_file(RECETAS_DIR, "recetas")
    if path and os.path.exists(path):
        try:
            df = pd.read_excel(path)
        except Exception as e:
            st.error(f"Error cargando recetas.xlsx: {e}")
            df = pd.DataFrame(columns=EXPECTED_COLUMNS)
    else:
        df = pd.DataFrame(columns=EXPECTED_COLUMNS)

    missing = [c for c in EXPECTED_COLUMNS if c not in df.columns]
    if missing:
        st.error(f"Recetas incompletas. Faltan columnas: {', '.join(missing)}")
    df = df.reindex(columns=EXPECTED_COLUMNS)

    if catalogo is not None and not df.empty:
        ctl_products = set(
            catalogo[catalogo["Tipo_venta"] == "CTL"]["Item"].dropna()
        )
        for prod in df["Producto_vendido"].dropna().unique():
            if prod not in ctl_products:
                st.warning(
                    f"'{prod}' en recetas no está definido como CTL en el catálogo."
                )

        catalog_items = set(catalogo["Item"].dropna())
        for ing in df["Ingrediente"].dropna().unique():
            if ing not in catalog_items:
                st.warning(
                    f"Ingrediente '{ing}' no existe en el catálogo."
                )

        dosis_map = catalogo.set_index("Item")["Dosis_ml"]
        df["Cantidad_usada"] = df["Ingrediente"].map(dosis_map)
    else:
        df["Cantidad_usada"] = None

    df = df[["Producto_vendido", "Ingrediente", "Cantidad_usada", "Unidad"]]
    return df


def recetas_module():
    st.title("Recetas de Productos Compuestos")
    st.info(
        """Las recetas sólo aplican a productos del catálogo con Tipo_venta = CTL.
        Cada fila representa un ingrediente necesario para preparar una unidad del
        producto compuesto.
        ✏️ La edición se realiza directamente en el archivo más reciente dentro de
        `data/recetas/`.
        """
    )

    catalogo = load_catalog()
    df_recetas = load_recetas(catalogo)
    st.dataframe(df_recetas)

    st.download_button(
        label="Descargar archivo de recetas", 
        data=to_excel_bytes(df_recetas),
        file_name="recetas.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )

    st.info(
        "**Formato requerido:**\n"
        "- Producto_vendido\n"
        "- Ingrediente\n"
        "- Unidad\n"
        "*(Cantidad_usada se toma automáticamente del catálogo)*"
    )

