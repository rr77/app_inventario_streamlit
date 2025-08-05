import streamlit as st
import os
from glob import glob
from datetime import datetime

from modules.catalogo import load_catalog
from modules.stock import load_last_cierre, calcular_stock_actual
from utils.pdf_report import generar_pdf_stock
from utils.path_utils import (
    REPORTES_PDF_DIR,
    AUDITORIA_AP_DIR,
    AUDITORIA_CI_DIR,
)


def _listar_pdfs(patron):
    archivos = sorted(glob(os.path.join(REPORTES_PDF_DIR, patron)), reverse=True)
    if not archivos:
        st.info("No hay reportes disponibles.")
        return
    for archivo in archivos:
        with open(archivo, "rb") as f:
            st.download_button(
                label=os.path.basename(archivo),
                data=f,
                file_name=os.path.basename(archivo),
                mime="application/pdf",
            )


def _listar_excels(folder):
    archivos = sorted(glob(os.path.join(folder, "*.xlsx")), reverse=True)
    if not archivos:
        st.info("No hay reportes disponibles.")
        return
    for archivo in archivos:
        with open(archivo, "rb") as f:
            st.download_button(
                label=os.path.basename(archivo),
                data=f,
                file_name=os.path.basename(archivo),
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            )


def _generar_reporte_stock(prefijo):
    cat = load_catalog()
    stock_inicial, _ = load_last_cierre()
    df_stock = calcular_stock_actual(cat, stock_inicial)
    nombre = f"{prefijo}_{datetime.today().strftime('%Y-%m-%d')}.pdf"
    ruta = os.path.join(REPORTES_PDF_DIR, nombre)
    pdf_bytes = generar_pdf_stock(df_stock, ruta)
    st.success(f"Reporte {prefijo} generado.")
    st.download_button(
        label="Descargar reporte recién generado",
        data=pdf_bytes,
        file_name=nombre,
        mime="application/pdf",
    )


def reportes_module():
    """Centro de reportes históricos y generación de nuevos informes."""
    st.title("Centro de Reportes")
    st.info(
        """
        Consulta y genera reportes diarios, semanales y mensuales del inventario.
        Los reportes diarios se producen en los módulos de auditoría de apertura y
        cierre; desde aquí puedes descargar el historial y generar resúmenes de stock
        semanales o mensuales cuando lo requieras.
        """
    )

    tab_diario, tab_semanal, tab_mensual = st.tabs(["Diarios", "Semanales", "Mensuales"])

    with tab_diario:
        sub_ap, sub_ci = st.tabs(["Apertura", "Cierre"])
        with sub_ap:
            ap_pdf, ap_excel = st.tabs(["PDF", "Excel"])
            with ap_pdf:
                _listar_pdfs("auditoria_apertura_*.pdf")
            with ap_excel:
                _listar_excels(AUDITORIA_AP_DIR)
        with sub_ci:
            ci_pdf, ci_excel = st.tabs(["PDF", "Excel"])
            with ci_pdf:
                _listar_pdfs("auditoria_cierre_*.pdf")
            with ci_excel:
                _listar_excels(AUDITORIA_CI_DIR)
        st.caption(
            "Para generar nuevos reportes diarios utilice los módulos de auditoría en el menú principal."
        )

    with tab_semanal:
        if st.button("Generar reporte semanal de stock"):
            _generar_reporte_stock("reporte_semanal")
        _listar_pdfs("reporte_semanal_*.pdf")

    with tab_mensual:
        if st.button("Generar reporte mensual de stock"):
            _generar_reporte_stock("reporte_mensual")
        _listar_pdfs("reporte_mensual_*.pdf")

