import streamlit as st
import pandas as pd
import os
import math
from utils.excel_tools import to_excel_bytes
from utils.unit_conversion import to_bottles
from utils.pdf_report import generar_pdf_stock
from utils.path_utils import (
    ENTRADAS_DIR,
    TRANSFERENCIAS_DIR,
    VENTAS_PROCESADAS_DIR,
    CIERRES_CONFIRMADOS_DIR,
    AUDITORIA_AP_DIR,
    AUDITORIA_CI_DIR,
    REPORTES_PDF_DIR,
    latest_file,
)
from modules.catalogo import load_catalog

ENTRADAS_FOLDER = ENTRADAS_DIR
TRANSFERENCIAS_FOLDER = TRANSFERENCIAS_DIR
VENTAS_PROCESADAS_FOLDER = VENTAS_PROCESADAS_DIR
CIERRES_CONFIRMADOS_FOLDER = CIERRES_CONFIRMADOS_DIR
AUDITORIA_AP_FOLDER = AUDITORIA_AP_DIR
AUDITORIA_CI_FOLDER = AUDITORIA_CI_DIR
REPORTES_PDF_FOLDER = REPORTES_PDF_DIR

LOW_STOCK_THRESHOLD = 3  # botellas


def load_all_entradas():
    archivos = [f for f in os.listdir(ENTRADAS_FOLDER) if f.endswith('.xlsx')]
    dfs = []
    for f in archivos:
        try:
            df = pd.read_excel(os.path.join(ENTRADAS_FOLDER, f))
            dfs.append(df)
        except:  # noqa: E722
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
        except:  # noqa: E722
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
        except:  # noqa: E722
            pass
    if dfs:
        return pd.concat(dfs, ignore_index=True)
    else:
        return pd.DataFrame(
            columns=[
                "Fecha",
                "Producto vendido",
                "Item usado",
                "Subcategoría",
                "Cantidad teórica consumida",
                "Ubicación de salida",
            ]
        )


def load_last_cierre():
    archivos = [f for f in os.listdir(CIERRES_CONFIRMADOS_FOLDER) if f.endswith('.xlsx')]
    if not archivos:
        return pd.DataFrame(columns=["Item", "Ubicación", "Cantidad"]), False
    archivos_sorted = sorted(archivos, reverse=True)
    df = pd.read_excel(os.path.join(CIERRES_CONFIRMADOS_FOLDER, archivos_sorted[0]))
    return df, True


def obtener_ultimo_movimiento():
    """Devuelve descripción del movimiento más reciente registrado."""
    movimientos = [
        (ENTRADAS_FOLDER, "Entrada", "entradas"),
        (TRANSFERENCIAS_FOLDER, "Transferencia", "transferencias"),
        (VENTAS_PROCESADAS_FOLDER, "Salida", "ventas_procesadas"),
        (AUDITORIA_AP_FOLDER, "Auditoría de apertura", "auditoria_apertura"),
        (AUDITORIA_CI_FOLDER, "Auditoría de cierre", "auditoria_cierre"),
    ]
    ultimo = None
    tipo = ""
    pref_ultimo = ""
    for folder, etiqueta, pref in movimientos:
        archivo = latest_file(folder, pref)
        if archivo:
            mtime = os.path.getmtime(archivo)
            if not ultimo or mtime > ultimo[0]:
                ultimo = (mtime, archivo)
                tipo = etiqueta
                pref_ultimo = pref
    if ultimo:
        fecha = (
            os.path.basename(ultimo[1])
            .replace(f"{pref_ultimo}_", "")
            .replace(".xlsx", "")
        )
        return f"{tipo} ({fecha})"
    return "Sin movimientos registrados"


def round_sig(x: float | None, sig: int = 2):
    if x is None or pd.isna(x) or x == 0:
        return x
    return round(x, sig - int(math.floor(math.log10(abs(x)))) - 1)


def stock_module():
    st.title("Stock Actual por Ubicación")
    st.info(
        """
    Visualiza el stock actual considerando todos los movimientos registrados a la fecha.
    El cálculo parte del último cierre confirmado.
    """
    )

    cat = load_catalog()
    if cat.empty or "Item" not in cat.columns:
        st.warning("No se encontró el catálogo o falta la columna 'Item'.")
        return
    stock_inicial, cierre_encontrado = load_last_cierre()
    if not cierre_encontrado:
        st.warning(
            "No se encontró un cierre confirmado. El stock se calcula desde cero."
        )
    ult_mov = obtener_ultimo_movimiento()
    st.caption(f"Último movimiento registrado: {ult_mov}")
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
                    cantidad = (
                        match.iloc[0]["Cantidad"]
                        if "Cantidad" in match.columns
                        else match.iloc[0].get("Físico Cierre", 0)
                    )
            # Sumar entradas a esa ubicación
            if not entradas.empty:
                entradas_sum = entradas[(entradas["Item"] == item) & (entradas["Ubicación destino"] == ubic)][
                    "Cantidad"
                ].sum()
                cantidad += entradas_sum
            # Transferencias: sumar si es destino, restar si es origen
            if not transferencias.empty:
                transfer_in = transferencias[(transferencias["Item"] == item) & (transferencias["Hacia"] == ubic)][
                    "Cantidad"
                ].sum()
                transfer_out = transferencias[(transferencias["Item"] == item) & (transferencias["Desde"] == ubic)][
                    "Cantidad"
                ].sum()
                cantidad += transfer_in - transfer_out
            # Ventas (consumo teórico): solo para Barra y Vinera
            if ubic in ["Barra", "Vinera"] and not ventas.empty:
                consumo = ventas[(ventas["Item usado"] == item) & (ventas["Ubicación de salida"] == ubic)][
                    "Cantidad teórica consumida"
                ].sum()
                cantidad -= consumo

            stock_botellas = to_bottles(item, cantidad, cat)
            subcat = (
                cat_filtrado[cat_filtrado["Item"] == item]["Subcategoría"].iloc[0]
                if not cat_filtrado[cat_filtrado["Item"] == item].empty
                else None
            )
            stock.append(
                {
                    "Producto": item,
                    "Subcategoría": subcat,
                    "Ubicación": ubic,
                    "Stock Botellas": round_sig(stock_botellas, 2),
                }
            )

    df_stock = pd.DataFrame(stock)
    df_stock = df_stock[df_stock["Stock Botellas"].notna()]

    # FILTRO POR UBICACIÓN
    ubicacion_sel = st.selectbox("Filtrar por ubicación", options=["TODAS"] + ubicaciones)
    if ubicacion_sel != "TODAS":
        df_stock = df_stock[df_stock["Ubicación"] == ubicacion_sel]

    # BÚSQUEDA POR NOMBRE DE PRODUCTO
    search_term = st.text_input("Buscar producto")
    if search_term:
        df_stock = df_stock[
            df_stock["Producto"].str.contains(search_term, case=False, na=False)
        ]

    # ESTADO SEGÚN STOCK
    def evaluar_estado(cant):
        if pd.isna(cant):
            return ""
        if cant < 0:
            return "⚠️ Negativo"
        if cant == 0:
            return "🔴 Agotado"
        if cant <= LOW_STOCK_THRESHOLD:
            return "🟡 Bajo stock"
        return "✅ OK"

    df_stock["Estado"] = df_stock["Stock Botellas"].apply(evaluar_estado)

    # ORDEN ASCENDENTE POR DEFECTO
    df_stock = df_stock.sort_values(by="Stock Botellas", ascending=True)

    # Estilos visuales para resaltar situaciones críticas
    def color_estado(row):
        estado = row["Estado"]
        if "Negativo" in estado:
            return ["background-color: #ffbdbd"] * len(row)
        if "Agotado" in estado:
            return ["background-color: #ffc9c9"] * len(row)
        if "Bajo" in estado:
            return ["background-color: #fff5ba"] * len(row)
        return [""] * len(row)

    st.dataframe(df_stock.style.apply(color_estado, axis=1), use_container_width=True)

    st.download_button(
        label="Descargar Stock Actual (Excel)",
        data=to_excel_bytes(df_stock),
        file_name="stock_actual.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )

    fecha_hoy = pd.Timestamp.today().strftime("%Y-%m-%d")
    pdfout = f"stock_{fecha_hoy}.pdf"
    pdf_bytes = generar_pdf_stock(
        df_stock, os.path.join(REPORTES_PDF_FOLDER, pdfout)
    )
    st.download_button(
        label="Descargar Stock Actual (PDF)",
        data=pdf_bytes,
        file_name=pdfout,
        mime="application/pdf",
    )
