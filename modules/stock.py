import streamlit as st
import pandas as pd
import os
from utils.excel_tools import to_excel_bytes
from utils.unit_conversion import to_bottles
from utils.path_utils import (
    CATALOGO_DIR,
    ENTRADAS_DIR,
    TRANSFERENCIAS_DIR,
    VENTAS_PROCESADAS_DIR,
    CIERRES_CONFIRMADOS_DIR,
    latest_file,
)

ENTRADAS_FOLDER = ENTRADAS_DIR
TRANSFERENCIAS_FOLDER = TRANSFERENCIAS_DIR
VENTAS_PROCESADAS_FOLDER = VENTAS_PROCESADAS_DIR
CIERRES_CONFIRMADOS_FOLDER = CIERRES_CONFIRMADOS_DIR

def load_all_entradas():
    archivos = [f for f in os.listdir(ENTRADAS_FOLDER) if f.endswith('.xlsx')]
    dfs = []
    for f in archivos:
        try:
            df = pd.read_excel(os.path.join(ENTRADAS_FOLDER, f))
            dfs.append(df)
        except:
            pass
    if dfs:
        return pd.concat(dfs, ignore_index=True)
    else:
        return pd.DataFrame(columns=["Fecha", "Item", "Subcategoría", "Ubicación destino", "Cantidad"])

def load_all_transferencias():
    archivos = [f for f in os.listdir(TRANSFERENCIAS_FOLDER) if f.endswith('.xlsx')]
    dfs = []
    for f in archivos:
        try:
            df = pd.read_excel(os.path.join(TRANSFERENCIAS_FOLDER, f))
            dfs.append(df)
        except:
            pass
    if dfs:
        return pd.concat(dfs, ignore_index=True)
    else:
        return pd.DataFrame(columns=["Fecha", "Item", "Desde", "Hacia", "Cantidad"])

def load_all_ventas():
    archivos = [f for f in os.listdir(VENTAS_PROCESADAS_FOLDER) if f.endswith('.xlsx')]
    dfs = []
    for f in archivos:
        try:
            df = pd.read_excel(os.path.join(VENTAS_PROCESADAS_FOLDER, f))
            dfs.append(df)
        except:
            pass
    if dfs:
        return pd.concat(dfs, ignore_index=True)
    else:
        return pd.DataFrame(columns=["Fecha", "Producto vendido", "Item usado", "Subcategoría", "Cantidad teórica consumida", "Ubicación de salida"])

def load_last_cierre():
    archivos = [f for f in os.listdir(CIERRES_CONFIRMADOS_FOLDER) if f.endswith('.xlsx')]
    if not archivos:
        return pd.DataFrame(columns=["Item", "Ubicación", "Cantidad"])
    archivos_sorted = sorted(archivos, reverse=True)
    df = pd.read_excel(os.path.join(CIERRES_CONFIRMADOS_FOLDER, archivos_sorted[0]))
    return df

def stock_module():
    st.title("Stock Actual por Ubicación")
    st.info("""
    Visualiza el stock actual considerando todos los movimientos registrados a la fecha.
    El cálculo parte del último cierre confirmado.
    """)

    cat_path = latest_file(CATALOGO_DIR, "catalogo")
    if not cat_path or not os.path.exists(cat_path):
        st.warning("No se encontró el catálogo.")
        return
    cat = pd.read_excel(cat_path)
    stock_inicial = load_last_cierre()
    entradas = load_all_entradas()
    transferencias = load_all_transferencias()
    ventas = load_all_ventas()

    ubicaciones = ["Almacén", "Barra", "Vinera"]
    # Excluir productos que sean cocteles/cocktails del stock
    cat_filtrado = cat[~cat["Item"].str.contains(r"(?i)c[oó]ctel(?:es)?|cocktail", na=False)]
    items = cat_filtrado["Item"].unique()

    stock = []
    for item in items:
        for ubic in ubicaciones:
            cantidad = 0.0
            # Cierre confirmado
            if not stock_inicial.empty:
                match = stock_inicial[(stock_inicial["Item"] == item) & (stock_inicial["Ubicación"] == ubic)]
                if not match.empty:
                    cantidad = match.iloc[0]["Cantidad"] if "Cantidad" in match.columns else match.iloc[0].get("Físico Cierre", 0)
            # Sumar entradas a esa ubicación
            if not entradas.empty:
                entradas_sum = entradas[(entradas["Item"] == item) & (entradas["Ubicación destino"] == ubic)]["Cantidad"].sum()
                cantidad += entradas_sum
            # Transferencias: sumar si es destino, restar si es origen
            if not transferencias.empty:
                transfer_in = transferencias[(transferencias["Item"] == item) & (transferencias["Hacia"] == ubic)]["Cantidad"].sum()
                transfer_out = transferencias[(transferencias["Item"] == item) & (transferencias["Desde"] == ubic)]["Cantidad"].sum()
                cantidad += transfer_in - transfer_out
            # Ventas (consumo teórico): solo para Barra y Vinera
            if ubic in ["Barra", "Vinera"] and not ventas.empty:
                consumo = ventas[(ventas["Item usado"] == item) & (ventas["Ubicación de salida"] == ubic)]["Cantidad teórica consumida"].sum()
                cantidad -= consumo

            stock_botellas = to_bottles(item, cantidad, cat)
            stock.append({
                "Item": item,
                "Ubicación": ubic,
                "Stock teórico (unidad base)": cantidad,
                "Stock equivalente (botellas)": round(stock_botellas, 2) if stock_botellas is not None else None,
            })

    df_stock = pd.DataFrame(stock)
    # eliminar filas sin stock para evitar mostrar ubicaciones innecesarias
    df_stock = df_stock[df_stock["Stock teórico (unidad base)"] != 0]

    # FILTRO POR UBICACIÓN
    ubicacion_sel = st.selectbox("Filtrar por ubicación", options=["TODAS"] + ubicaciones)
    if ubicacion_sel != "TODAS":
        df_stock = df_stock[df_stock["Ubicación"] == ubicacion_sel]

    df_display = df_stock.copy()
    df_display["Stock equivalente (botellas)"] = df_display["Stock equivalente (botellas)"].apply(lambda x: "" if pd.isna(x) else x)

    st.dataframe(df_display, use_container_width=True)

    st.download_button(
        label="Descargar Stock Actual (Excel)",
        data=to_excel_bytes(df_stock),
        file_name="stock_actual.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
