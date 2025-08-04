import streamlit as st
import pandas as pd
import os
from datetime import datetime
from utils.pdf_report import generar_pdf_cierre, generar_pdf_apertura  # deja tu stub
from utils.excel_tools import to_excel_bytes  # <<< AGREGA ESTA LINEA

CATALOGO_PATH = "catalogo/catalogo.xlsx"
ENTRADAS_FOLDER = "entradas/"
TRANSFERENCIAS_FOLDER = "transferencias/"
VENTAS_PROCESADAS_FOLDER = "ventas_procesadas/"
CIERRES_CONFIRMADOS_FOLDER = "cierres_confirmados/"
AUDITORIA_AP_FOLDER = "auditorias/apertura/"
AUDITORIA_CI_FOLDER = "auditorias/cierre/"
REPORTES_PDF_FOLDER = "reportes_pdf/"

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
    df_new.to_excel(path, index=False)

def auditoria_apertura():
    st.title("Auditoría de Apertura")
    st.info("""
    Carga el archivo Excel con el conteo físico de apertura (realizado al iniciar el día).
    Si el archivo tiene columna 'Requisicion', las transferencias declaradas se registrarán automáticamente.
    """)
    fecha = st.date_input("Fecha de auditoría de apertura", value=datetime.today())
    archivo = st.file_uploader("Selecciona el archivo de conteo de apertura (Excel plantilla oficial)", type=["xlsx"])
    if archivo and st.button("Procesar auditoría de apertura"):
        df = pd.read_excel(archivo)
        requeridas = ["Fecha", "Item", "Subcategoría", "Ubicación", "Conteo Apertura"]
        for req in requeridas:
            if req not in df.columns:
                st.error(f"Falta columna requerida: {req}")
                return
        if "Requisicion" not in df.columns:
            df["Requisicion"] = 0
        registrar_requisiciones(df, fecha.strftime("%Y-%m-%d"))
        archivos = [f for f in os.listdir(CIERRES_CONFIRMADOS_FOLDER) if f.endswith('.xlsx')]
        if archivos:
            ult_cierre = os.path.join(CIERRES_CONFIRMADOS_FOLDER, sorted(archivos, reverse=True)[0])
            prev = pd.read_excel(ult_cierre)
        else:
            prev = pd.DataFrame(columns=["Item", "Ubicación", "Físico Cierre"])
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
        df_res.to_excel(os.path.join(AUDITORIA_AP_FOLDER, outfile), index=False)
        generar_pdf_apertura(df_res, os.path.join(REPORTES_PDF_FOLDER, pdfout))
        st.success("Auditoría procesada y registrada.")
        st.dataframe(df_res)
        # USAR EL NUEVO PATRÓN PARA DESCARGA
        st.download_button("Descargar auditoría (Excel)", data=to_excel_bytes(df_res),
            file_name=outfile)
        with open(os.path.join(REPORTES_PDF_FOLDER, pdfout), "rb") as f:
            st.download_button("Descargar auditoría (PDF)", data=f, file_name=pdfout, mime="application/pdf")

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
    archivo = st.file_uploader("Selecciona el archivo de conteo de cierre (Excel plantilla oficial)", type=["xlsx"])
    if archivo and st.button("Procesar auditoría de cierre"):
        df = pd.read_excel(archivo)
        requeridas = ["Fecha", "Item", "Subcategoría", "Ubicación", "Conteo Apertura", "Conteo Cierre"]
        for req in requeridas:
            if req not in df.columns:
                st.error(f"Falta columna requerida: {req}")
                return
        if "Requisicion" not in df.columns:
            df["Requisicion"] = 0
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
            if ubic in ["Barra", "Vinera"]:
                consumo = ventas[(ventas["Item usado"] == item) & (ventas["Ubicación de salida"] == ubic)]["Cantidad teórica consumida"].sum()
            else:
                consumo = 0
            teorico_cierre = apertura + entradas_sum + transf_in - transf_out - consumo
            diferencia = cierre_fisico - teorico_cierre
            pct = (diferencia / teorico_cierre) * 100 if teorico_cierre != 0 else 0
            result.append({
                "Item": item,
                "Ubicación": ubic,
                "Apertura": apertura,
                "Entradas": entradas_sum,
                "Transf In": transf_in,
                "Transf Out": transf_out,
                "Salida Teórica": consumo,
                "Teórico Cierre": teorico_cierre,
                "Físico Cierre": cierre_fisico,
                "Diferencia": diferencia,
                "%": round(pct, 2)
            })
        df_res = pd.DataFrame(result)
        outfile = f"auditoria_cierre_{fecha.strftime('%Y-%m-%d')}.xlsx"
        pdfout = outfile.replace('.xlsx', '.pdf')
        df_res.to_excel(os.path.join(AUDITORIA_CI_FOLDER, outfile), index=False)
        generar_pdf_cierre(df_res, os.path.join(REPORTES_PDF_FOLDER, pdfout))
        st.success("Auditoría de cierre procesada y registrada.")
        st.dataframe(df_res)
        # USAR EL NUEVO PATRÓN PARA DESCARGA
        st