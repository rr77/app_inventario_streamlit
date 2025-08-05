import os
from datetime import datetime

import pandas as pd
import streamlit as st

from utils.excel_tools import to_excel_bytes
from utils.path_utils import VENTAS_PROCESADAS_DIR
from modules.catalogo import load_catalog
from modules.recetas import load_recetas


VENTAS_PROCESADAS_FOLDER = VENTAS_PROCESADAS_DIR

PRODUCTO_NAMES = [
    "producto vendido",
    "item vendido",
    "item",
    "producto",
    "descripcion",
    "descripción",
]

SUBCAT_NAMES = [
    "subcategoria",
    "subcategoría",
    "subcategory",
    "sub cat",
    "subcat",
    "línea",
    "linea",
]

CANTIDAD_NAMES = [
    "cantidad",
    "cantidad vendida",
    "c. vendida",
    "unidades",
    "qty",
]


def seleccionar_columna(df: pd.DataFrame, label: str, posibles: list[str]) -> str:
    posibles_lower = [p.lower() for p in posibles]
    detected = next(
        (c for c in df.columns if c.strip().lower() in posibles_lower), None
    )
    index = df.columns.get_loc(detected) if detected in df.columns else 0
    return st.selectbox(label, df.columns, index=index)


def procesar_ventas(
    df_ventas: pd.DataFrame,
    prod_col: str,
    subcat_col: str,
    cant_col: str | None,
    catalogo: pd.DataFrame,
    recetas: pd.DataFrame,
    fecha: datetime,
) -> pd.DataFrame:
    resultado: list[dict] = []

    for _, row in df_ventas.iterrows():
        nombre = str(row[prod_col]).strip()
        subcat = str(row[subcat_col]).strip()
        cantidad = row[cant_col] if cant_col else 1

        match = catalogo[
            (catalogo["Nombre"] == nombre) & (catalogo["Subcategoría"] == subcat)
        ]
        if match.empty:
            st.warning(f"Producto '{nombre}' / '{subcat}' no está en el catálogo. Se omite.")
            continue

        tipo = match.iloc[0]["Tipo_venta"]
        unidad = match.iloc[0]["Unidad"]

        if tipo == "CTL":
            receta = recetas[recetas["Producto_vendido"] == nombre]
            if receta.empty:
                st.warning(f"No hay receta para '{nombre}'. Se omite.")
                continue
            for _, ing in receta.iterrows():
                resultado.append(
                    {
                        "Fecha": fecha,
                        "Producto_vendido": nombre,
                        "Ingrediente": ing["Ingrediente"],
                        "Unidad": ing["Unidad"],
                        "Cantidad_consumida": ing["Cantidad_usada"] * cantidad,
                    }
                )
        elif tipo == "BOT":
            resultado.append(
                {
                    "Fecha": fecha,
                    "Producto_vendido": nombre,
                    "Ingrediente": nombre,
                    "Unidad": unidad,
                    "Cantidad_consumida": cantidad,
                }
            )
        elif tipo == "TRG":
            dosis = match.iloc[0]["Dosis_ml"]
            resultado.append(
                {
                    "Fecha": fecha,
                    "Producto_vendido": nombre,
                    "Ingrediente": nombre,
                    "Unidad": "ml",
                    "Cantidad_consumida": dosis * cantidad,
                }
            )
        else:
            st.warning(f"Tipo_venta desconocido para '{nombre}'. Se omite.")

    return pd.DataFrame(resultado)


def ventas_module():
    st.title("Procesador de Ventas")
    st.info(
        """Sube el Excel del POS (ventas del día). El sistema usará el catálogo y
        las recetas para calcular el consumo teórico de inventario. La identificación
        de productos se realiza exclusivamente por Nombre y Subcategoría."""
    )

    catalogo = load_catalog()
    if catalogo.empty:
        st.warning("El catálogo está vacío. No se pueden procesar ventas.")
        return

    recetas = load_recetas(catalogo)

    fecha = st.date_input("Selecciona la fecha de las ventas", value=datetime.today())
    archivo = st.file_uploader("Selecciona archivo Excel de ventas...", type=["xlsx"])

    if archivo:
        try:
            # La primera fila del archivo generado por el POS viene vacía,
            # por lo que se usa header=1 para ignorarla y tomar los nombres
            # de las columnas de la segunda fila.
            df_ventas = pd.read_excel(archivo, header=1)
        except Exception as e:
            st.error(f"Error leyendo archivo de ventas: {e}")
            return

        st.dataframe(df_ventas)

        prod_col = seleccionar_columna(
            df_ventas, "Columna de producto vendido", PRODUCTO_NAMES
        )
        subcat_col = seleccionar_columna(
            df_ventas, "Columna de subcategoría", SUBCAT_NAMES
        )
        cant_col = seleccionar_columna(
            df_ventas, "Columna de cantidad vendida", CANTIDAD_NAMES + ["(ninguna)"]
        )
        if cant_col == "(ninguna)":
            cant_col = None

        if st.button("Procesar ventas"):
            df_proc = procesar_ventas(
                df_ventas, prod_col, subcat_col, cant_col, catalogo, recetas, fecha
            )
            if df_proc.empty:
                st.warning("No se generó consumo. Revisa los datos.")
            else:
                output_file = f"ventas_procesadas_{fecha.strftime('%Y-%m-%d')}.xlsx"
                out_path = os.path.join(VENTAS_PROCESADAS_FOLDER, output_file)
                df_proc.to_excel(out_path, index=False)
                st.success(f"Ventas procesadas. Archivo guardado como: {output_file}")
                st.dataframe(df_proc)
                st.download_button(
                    label="Descargar consumo teórico", 
                    data=to_excel_bytes(df_proc),
                    file_name=output_file,
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                )

