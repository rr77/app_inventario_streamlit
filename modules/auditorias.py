import streamlit as st
import pandas as pd
import os
from datetime import datetime
from utils.pdf_report import generar_pdf_cierre, generar_pdf_apertura  # deja tu stub
from utils.excel_tools import to_excel_bytes
from utils.unit_conversion import to_ml
from utils.path_utils import (
    CATALOGO_DIR,
    ENTRADAS_DIR,
    TRANSFERENCIAS_DIR,
    VENTAS_PROCESADAS_DIR,
    CIERRES_CONFIRMADOS_DIR,
    AUDITORIA_AP_DIR,
    AUDITORIA_CI_DIR,
    REPORTES_PDF_DIR,
    latest_file,
)

ENTRADAS_FOLDER = ENTRADAS_DIR
TRANSFERENCIAS_FOLDER = TRANSFERENCIAS_DIR
VENTAS_PROCESADAS_FOLDER = VENTAS_PROCESADAS_DIR
CIERRES_CONFIRMADOS_FOLDER = CIERRES_CONFIRMADOS_DIR
AUDITORIA_AP_FOLDER = AUDITORIA_AP_DIR
AUDITORIA_CI_FOLDER = AUDITORIA_CI_DIR
REPORTES_PDF_FOLDER = REPORTES_PDF_DIR

# Ubicaciones disponibles para las auditorías
UBICACIONES = ["Almacén", "Barra", "Vinera"]

def registrar_requisiciones(df_audit, fecha):
    df_requis = df_audit[(df_audit["Requisicion"] > 0)]
    if df_requis.empty:
        return
    registros = []
    for idx, row in df_requis.iterrows():
        registros.append({
            "Fecha": fecha,
            "Item": row["Item"],
            "Desde": "Almacén",
            "Hacia": row["Ubicación"],
            "Cantidad": row["Requisicion"]
        })
    archivo = f"transferencias_{fecha}.xlsx"
    path = os.path.join(TRANSFERENCIAS_FOLDER, archivo)
    if os.path.exists(path):
        df_old = pd.read_excel(path)
        df_new = pd.concat([df_old, pd.DataFrame(registros)], ignore_index=True)
    else:
        df_new = pd.DataFrame(registros)
    df_new = df_new.drop_duplicates(subset=["Fecha", "Item", "Desde", "Hacia", "Cantidad"], keep="first")
    try:
        with pd.ExcelWriter(path, engine="xlsxwriter") as writer:
            df_new.to_excel(writer, index=False)
    except Exception as e:
        st.error(f"Error guardando transferencias: {e}")

def auditoria_apertura():
    st.title("Auditoría de Apertura")
    st.info("""
    Carga el archivo Excel con el conteo físico de apertura (realizado al iniciar el día).
    Si el archivo tiene columna 'Requisicion', las transferencias declaradas se registrarán automáticamente.
    """)
    fecha = st.date_input("Fecha de auditoría de apertura", value=datetime.today())
    ubic_sel = st.selectbox(
        "Ubicación de la auditoría",
        ["General"] + UBICACIONES,
    )
    archivo = st.file_uploader(
        "Selecciona el archivo de conteo de apertura (Excel plantilla oficial)",
        type=["xlsx"],
    )
    if archivo and st.button("Procesar auditoría de apertura"):
        df = pd.read_excel(archivo)
        requeridas = ["Fecha", "Item", "Subcategoría", "Conteo Apertura"]
        if ubic_sel == "General":
            requeridas.append("Ubicación")
        for req in requeridas:
            if req not in df.columns:
                st.error(f"Falta columna requerida: {req}")
                return
        if ubic_sel != "General":
            df["Ubicación"] = ubic_sel
        if "Requisicion" not in df.columns:
            df["Requisicion"] = 0

        cat_path = latest_file(CATALOGO_DIR, "catalogo")
        if not cat_path or not os.path.exists(cat_path):
            st.error("No se encontró el catálogo para validar unidades.")
            return
        cat = pd.read_excel(cat_path)
        df["Conteo Apertura"] = df.apply(lambda r: to_ml(r["Item"], r["Conteo Apertura"], cat), axis=1)
        df["Requisicion"] = df.apply(lambda r: to_ml(r["Item"], r["Requisicion"], cat), axis=1)

        registrar_requisiciones(df, fecha.strftime("%Y-%m-%d"))
        archivos = [f for f in os.listdir(CIERRES_CONFIRMADOS_FOLDER) if f.endswith('.xlsx')]
        if archivos:
            ult_cierre = os.path.join(CIERRES_CONFIRMADOS_FOLDER, sorted(archivos, reverse=True)[0])
            prev = pd.read_excel(ult_cierre)
        else:
            prev = pd.DataFrame(columns=["Item", "Ubicación", "Físico Cierre"])
        if prev.empty:
            st.warning("No se encontró auditoría de cierre del día anterior.")
        result = []
        for idx, row in df.iterrows():
            cierre_prev = prev[
                (prev["Item"] == row["Item"]) &
                (prev["Ubicación"] == row["Ubicación"])
            ]
            cierre_anterior = float(cierre_prev.iloc[0]["Físico Cierre"]) if not cierre_prev.empty else 0
            diferencia = float(row["Conteo Apertura"]) - cierre_anterior
            result.append({
                "Item": row["Item"],
                "Ubicación": row["Ubicación"],
                "Cierre anterior": cierre_anterior,
                "Apertura actual": row["Conteo Apertura"],
                "Diferencia": diferencia
            })
        df_res = pd.DataFrame(result)
        outfile = f"auditoria_apertura_{fecha.strftime('%Y-%m-%d')}.xlsx"
        pdfout = outfile.replace('.xlsx', '.pdf')
        out_path = os.path.join(AUDITORIA_AP_FOLDER, outfile)
        try:
            with pd.ExcelWriter(out_path, engine="xlsxwriter") as writer:
                df_res.to_excel(writer, index=False)
            pdf_bytes = generar_pdf_apertura(
                df_res, os.path.join(REPORTES_PDF_FOLDER, pdfout)
            )
        except Exception as e:
            st.error(f"Error guardando auditoría: {e}")
            return
        st.success("Auditoría procesada y registrada.")
        st.dataframe(df_res)
        # USAR EL NUEVO PATRÓN PARA DESCARGA
        st.download_button("Descargar auditoría (Excel)", data=to_excel_bytes(df_res), file_name=outfile)
        st.download_button("Descargar auditoría (PDF)", data=pdf_bytes, file_name=pdfout, mime="application/pdf")

def auditoria_cierre():
    st.title("Auditoría de Cierre")
    st.info("""
    Carga el archivo Excel con el conteo físico nocturno y 'Requisicion' (plantilla oficial).
    El sistema:
    - Calcula el stock teórico de cierre,
    - Lo compara con el físico,
    - Registra transferencias internas (si las hay en 'Requisicion'),
    - Genera un reporte detallado.
    """)
    fecha = st.date_input("Fecha de auditoría de cierre", value=datetime.today())
    ubic_sel = st.selectbox(
        "Ubicación de la auditoría",
        ["General"] + UBICACIONES,
    )
    archivo = st.file_uploader(
        "Selecciona el archivo de conteo de cierre (Excel plantilla oficial)",
        type=["xlsx"],
    )
    if archivo and st.button("Procesar auditoría de cierre"):
        df = pd.read_excel(archivo)
        requeridas = ["Fecha", "Item", "Subcategoría", "Conteo Cierre"]
        if ubic_sel == "General":
            requeridas.append("Ubicación")
        for req in requeridas:
            if req not in df.columns:
                st.error(f"Falta columna requerida: {req}")
                return
        if ubic_sel != "General":
            df["Ubicación"] = ubic_sel
        if "Requisicion" not in df.columns:
            df["Requisicion"] = 0

        # Intentar cargar la auditoría de apertura correspondiente
        apertura_arch = os.path.join(
            AUDITORIA_AP_FOLDER,
            f"auditoria_apertura_{fecha.strftime('%Y-%m-%d')}.xlsx",
        )
        if os.path.exists(apertura_arch):
            df_open = pd.read_excel(apertura_arch)
            if "Conteo Apertura" in df.columns:
                df = df.drop(columns=["Conteo Apertura"])
            df = df.merge(
                df_open[["Item", "Ubicación", "Conteo Apertura"]],
                on=["Item", "Ubicación"],
                how="left",
            )
            df["Conteo Apertura"] = df["Conteo Apertura"].fillna(0)
        else:
            df_open = pd.DataFrame(columns=["Item", "Ubicación", "Conteo Apertura"])
            df["Conteo Apertura"] = 0
            st.info(
                "No se encontró auditoría de apertura para la fecha; se asume Conteo Apertura = 0."
            )

        cat_path = latest_file(CATALOGO_DIR, "catalogo")
        if not cat_path or not os.path.exists(cat_path):
            st.error("No se encontró el catálogo para validar unidades.")
            return
        cat = pd.read_excel(cat_path)
        for col in ["Conteo Cierre", "Requisicion"]:
            df[col] = df.apply(lambda r: to_ml(r["Item"], r[col], cat), axis=1)
        if "Conteo Apertura" in df.columns:
            df["Conteo Apertura"] = df.apply(
                lambda r: to_ml(r["Item"], r["Conteo Apertura"], cat), axis=1
            )

        registrar_requisiciones(df, fecha.strftime("%Y-%m-%d"))

        # Cargar los movimientos diarios relevantes
        entradas_arch = os.path.join(ENTRADAS_FOLDER, f"entradas_{fecha.strftime('%Y-%m-%d')}.xlsx")
        if os.path.exists(entradas_arch):
            entradas = pd.read_excel(entradas_arch)
        else:
            entradas = pd.DataFrame(columns=["Fecha", "Item", "Subcategoría", "Ubicación destino", "Cantidad"])

        trans_arch = os.path.join(TRANSFERENCIAS_FOLDER, f"transferencias_{fecha.strftime('%Y-%m-%d')}.xlsx")
        if os.path.exists(trans_arch):
            trans = pd.read_excel(trans_arch)
        else:
            trans = pd.DataFrame(columns=["Fecha", "Item", "Desde", "Hacia", "Cantidad"])

        ventas_arch = os.path.join(VENTAS_PROCESADAS_FOLDER, f"ventas_procesadas_{fecha.strftime('%Y-%m-%d')}.xlsx")
        if os.path.exists(ventas_arch):
            ventas = pd.read_excel(ventas_arch)
        else:
            ventas = pd.DataFrame(columns=["Fecha", "Producto vendido", "Item usado", "Subcategoría",
                                           "Cantidad teórica consumida", "Ubicación de salida"])

        result = []
        for idx, row in df.iterrows():
            item, ubic = row["Item"], row["Ubicación"]
            apertura = float(row["Conteo Apertura"])
            cierre_fisico = float(row["Conteo Cierre"])
            entradas_sum = entradas[(entradas["Item"] == item) & (entradas["Ubicación destino"] == ubic)]["Cantidad"].sum()
            transf_in = trans[(trans["Item"] == item) & (trans["Hacia"] == ubic)]["Cantidad"].sum()
            transf_out = trans[(trans["Item"] == item) & (trans["Desde"] == ubic)]["Cantidad"].sum()
            transf_netas = transf_in - transf_out
            if ubic in ["Barra", "Vinera"]:
                consumo = ventas[(ventas["Item usado"] == item) & (ventas["Ubicación de salida"] == ubic)]["Cantidad teórica consumida"].sum()
            else:
                consumo = 0
            teorico_cierre = apertura + entradas_sum + transf_netas - consumo
            diferencia = cierre_fisico - teorico_cierre
            pct = (diferencia / teorico_cierre) * 100 if teorico_cierre != 0 else 0
            result.append({
                "Item": item,
                "Ubicación": ubic,
                "Apertura": apertura,
                "Entradas": entradas_sum,
                "Transferencias Netas": transf_netas,
                "Salida Teórica": consumo,
                "Teórico Cierre": teorico_cierre,
                "Físico Cierre": cierre_fisico,
                "Diferencia": diferencia,
                "%": round(pct, 2)
            })
        df_res = pd.DataFrame(result)
        outfile = f"auditoria_cierre_{fecha.strftime('%Y-%m-%d')}.xlsx"
        pdfout = outfile.replace('.xlsx', '.pdf')
        out_path = os.path.join(AUDITORIA_CI_FOLDER, outfile)
        try:
            with pd.ExcelWriter(out_path, engine="xlsxwriter") as writer:
                df_res.to_excel(writer, index=False)
            pdf_bytes = generar_pdf_cierre(
                df_res, os.path.join(REPORTES_PDF_FOLDER, pdfout)
            )
        except Exception as e:
            st.error(f"Error guardando auditoría: {e}")
            return
        st.success("Auditoría de cierre procesada y registrada.")
        st.dataframe(df_res)
        st.download_button("Descargar auditoría (Excel)", data=to_excel_bytes(df_res), file_name=outfile)
        st.download_button("Descargar auditoría (PDF)", data=pdf_bytes, file_name=pdfout, mime="application/pdf")
