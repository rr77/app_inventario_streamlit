import streamlit as st
import pandas as pd
import os
from datetime import datetime
from utils.excel_tools import to_excel_bytes  # Agrega esta línea
from utils.units import to_ml, to_bottles

CATALOGO_PATH = "catalogo/catalogo.xlsx"
RECETAS_PATH = "recetas/recetas.xlsx"
VENTAS_PROCESADAS_FOLDER = "ventas_procesadas/"

VINERA_SUBCATEGORIAS = set([
    "Blancos", "Tintos", "Espumantes", "Rosados", "Spirits & Wine"
])

def load_catalogo():
    return pd.read_excel(CATALOGO_PATH)

def load_recetas():
    xls = pd.ExcelFile(RECETAS_PATH)
    recetas = pd.read_excel(xls, "Recetas")
    reglas = pd.read_excel(xls, "ReglasEst")
    return recetas, reglas

def inferir_ubicacion(row, catalogo):
    prod = row["Producto vendido"]
    subcat = ""
    info = catalogo[catalogo["Item"] == prod]
    if not info.empty:
        subcat = str(info.iloc[0]["Subcategoría"])
    if subcat in VINERA_SUBCATEGORIAS:
        return "Vinera"
    else:
        return "Barra"

def procesar_ventas(df_ventas, df_recetas, df_reglas, catalogo, fecha_asignada):
    if "Producto vendido" not in df_ventas.columns:
        if "Item" in df_ventas.columns:
            df_ventas["Producto vendido"] = df_ventas["Item"]
        else:
            raise Exception("El archivo no tiene columna 'Producto vendido' ni 'Item'.")

    if "Cantidad vendida" not in df_ventas.columns:
        if "C. Vendida" in df_ventas.columns:
            df_ventas["Cantidad vendida"] = df_ventas["C. Vendida"]
        else:
            df_ventas["Cantidad vendida"] = 1  # Por defecto

    if "Fecha" not in df_ventas.columns:
        df_ventas["Fecha"] = fecha_asignada

    # Asigna la ubicación según subcategoría (regla especial)
    df_ventas["Ubicación de salida"] = df_ventas.apply(
        lambda r: inferir_ubicacion(r, catalogo), axis=1
    )

    result = []
    for idx, row in df_ventas.iterrows():
        prod_vendido = row["Producto vendido"]
        cantidad_vendida = row["Cantidad vendida"]
        fecha = row["Fecha"]
        ubic = row["Ubicación de salida"]

        recetas_match = df_recetas[df_recetas["Producto vendido"] == prod_vendido]
        if not recetas_match.empty:
            for _, rec in recetas_match.iterrows():
                item = rec["Item usado"]
                subcat = rec["Subcategoría"]
                cant_unit = rec["Cantidad usada"]
                cant_ml = to_ml(catalogo, item, cant_unit)
                total_ml = cant_ml * cantidad_vendida
                result.append({
                    "Fecha": fecha,
                    "Producto vendido": prod_vendido,
                    "Item usado": item,
                    "Subcategoría": subcat,
                    "Cantidad teórica consumida": total_ml,
                    "Cantidad botellas consumidas": to_bottles(catalogo, item, total_ml),
                    "Ubicación de salida": ubic
                })
        else:
            item_info = catalogo[catalogo["Item"] == prod_vendido]
            if not item_info.empty:
                subcat = item_info.iloc[0]["Subcategoría"]
                regla = df_reglas[df_reglas["Subcategoría"] == subcat]
                if not regla.empty:
                    cant_std = regla.iloc[0]["Cantidad estándar usada"]
                    cant_ml = to_ml(catalogo, prod_vendido, cant_std)
                    total_ml = cant_ml * cantidad_vendida
                    result.append({
                        "Fecha": fecha,
                        "Producto vendido": prod_vendido,
                        "Item usado": prod_vendido,
                        "Subcategoría": subcat,
                        "Cantidad teórica consumida": total_ml,
                        "Cantidad botellas consumidas": to_bottles(catalogo, prod_vendido, total_ml),
                        "Ubicación de salida": ubic
                    })
    return pd.DataFrame(result)

def ventas_module():
    st.title("Procesador de Ventas (Consumo Teórico)")
    st.info(
        """Sube el Excel del POS (ventas del día).
        El sistema calculará el consumo teórico de inventario usando las recetas y registrará todo en `/ventas_procesadas/`.
        El archivo POS puede tener cualquier cabecera: mapea automáticamente las columnas relevantes.

        **Regla de ubicación de salida:**
        Si la subcategoría es Blancos, Tintos, Espumantes, Rosados o Spirits & Wine: Vinera.
        Si no: Barra.
        """
    )

    catalogo = load_catalogo()
    if catalogo.empty:
        st.warning("El catálogo está vacío. No se pueden procesar ventas.")
        return

    df_recetas, df_reglas = load_recetas()
    st.markdown(
        """
    **El archivo POS puede tener estas columnas:**
    - Item (producto vendido)
    - C. Vendida (cantidad vendida)
    - (Opcional) Ubicación de salida
    - (Opcional) Fecha (si no, se asigna aquí)
    """
    )

    fecha = st.date_input("Selecciona la fecha de las ventas", value=datetime.today())
    archivo = st.file_uploader("Selecciona archivo Excel de ventas POS...", type=["xlsx"])

    if archivo:
        try:
            # Algunos archivos exportados del POS tienen la primera fila vacía y
            # los nombres de columnas en la segunda fila. Intentamos cargar el
            # Excel normalmente y, si no encontramos la columna "categoria",
            # volvemos a leer usando la segunda fila como cabecera.
            df_ventas = pd.read_excel(archivo)
            cat_col = next((c for c in df_ventas.columns if c.lower().strip() == "categoria"), None)
            if cat_col is None:
                # Reintenta asumiendo que la cabecera está en la segunda fila
                df_ventas = pd.read_excel(archivo, header=1)
                cat_col = next((c for c in df_ventas.columns if c.lower().strip() == "categoria"), None)
            if cat_col is None:
                st.error("El archivo de ventas debe tener una columna 'categoria'.")
                return
            df_ventas = df_ventas[
                df_ventas[cat_col].astype(str).str.strip().str.lower() == "licores"
            ]
            st.dataframe(df_ventas)
            if st.button("Procesar ventas y calcular consumo teórico"):
                df_procesado = procesar_ventas(df_ventas, df_recetas, df_reglas, catalogo, fecha)
                if not df_procesado.empty:
                    output_file = f"ventas_procesadas_{fecha.strftime('%Y-%m-%d')}.xlsx"
                    out_path = os.path.join(VENTAS_PROCESADAS_FOLDER, output_file)
                    df_procesado.to_excel(out_path, index=False)
                    st.success(f"Ventas procesadas. Archivo guardado como: {output_file}")
                    st.dataframe(df_procesado)
                    st.download_button(
                        label="Descargar consumo teórico procesado",
                        data=to_excel_bytes(df_procesado),
                        file_name=output_file,
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    )
                else:
                    st.warning("No se procesó ninguna venta. ¿Están las recetas/reglas bien definidas?")
        except Exception as e:
            st.error(f"Error procesando archivo de ventas: {e}")

