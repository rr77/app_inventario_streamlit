import streamlit as st
import pandas as pd
import os
from glob import glob

CARPETAS = {
    "Entradas": "entradas/",
    "Transferencias": "transferencias/",
    "Ventas procesadas": "ventas_procesadas/",
    "Auditoría apertura": "auditorias/apertura/",
    "Auditoría cierre": "auditorias/cierre/",
    "Cierres confirmados": "cierres_confirmados/"
}

def cargar_historial(tipo, path):
    archivos = glob(os.path.join(path, "*.xlsx"))
    registros = []
    for archivo in archivos:
        try:
            df = pd.read_excel(archivo)
            df["Origen archivo"] = os.path.basename(archivo)
            df["Tipo operación"] = tipo
            # Estandariza columnas comunes (Item, Ubicación, Fecha, Subcategoría si existe)
            if "Ubicación destino" in df.columns and "Ubicación" not in df.columns:
                df["Ubicación"] = df["Ubicación destino"]
            if "Hacia" in df.columns and "Ubicación" not in df.columns:
                df["Ubicación"] = df["Hacia"]  # solo para transferencias de llegada
            if "Conteo Apertura" in df.columns or "Conteo Cierre" in df.columns:
                if "Ubicación" not in df.columns and "Ubicación" in df:
                    df["Ubicación"] = df["Ubicación"]
            registros.append(df)
        except Exception as e:
            st.warning(f"No fue posible leer {archivo}: {e}")
    if registros:
        df = pd.concat(registros, ignore_index=True)
        # Normaliza algunas columnas
        for col in ["Fecha", "Item", "Ubicación", "Subcategoría"]:
            if col not in df.columns:
                df[col] = '' if col != "Fecha" else None
        return df
    else:
        return pd.DataFrame(columns=["Fecha","Item","Ubicación","Subcategoría","Tipo operación","Origen archivo"])

def historial_module():
    st.title("Historial integrado de movimientos y auditorías")

    st.info("""
        Consulta todos los movimientos y auditorías respaldados en el sistema. 
        Filtra por ubicación, ítem, subcategoría y descarga los datos para supervisión o análisis.
    """)

    # Selección tipo de operación
    tipo_sel = st.selectbox("¿Qué movimientos ver?", ["Todos"] + list(CARPETAS.keys()))

    # Carga el historial de uno o todos los tipos
    if tipo_sel == "Todos":
        dfs = []
        for tipo, path in CARPETAS.items():
            df_tipo = cargar_historial(tipo, path)
            dfs.append(df_tipo)
        df_hist = pd.concat(dfs, ignore_index=True)
    else:
        df_hist = cargar_historial(tipo_sel, CARPETAS[tipo_sel])

    if df_hist.empty:
        st.info("No hay movimientos o auditorías en esa categoría todavía.")
        return

    # Filtros dinámicos
    ubicaciones = sorted(df_hist["Ubicación"].dropna().unique())
    items = sorted(df_hist["Item"].dropna().unique())
    subcats = sorted(df_hist["Subcategoría"].dropna().unique())

    col1, col2, col3 = st.columns(3)
    filtro_ubic = col1.selectbox("Filtrar por Ubicación", ["Todas"] + ubicaciones)
    filtro_item = col2.selectbox("Filtrar por Item", ["Todos"] + items)
    filtro_subcat = col3.selectbox("Filtrar por Subcategoría", ["Todas"] + subcats)

    df_filtrado = df_hist.copy()
    if filtro_ubic != "Todas":
        df_filtrado = df_filtrado[df_filtrado["Ubicación"] == filtro_ubic]
    if filtro_item != "Todos":
        df_filtrado = df_filtrado[df_filtrado["Item"] == filtro_item]
    if filtro_subcat != "Todas":
        df_filtrado = df_filtrado[df_filtrado["Subcategoría"] == filtro_subcat]

    st.dataframe(df_filtrado, use_container_width=True)

    st.download_button(
        label="Descargar historial filtrado (Excel)",
        data=df_filtrado.to_excel(index=False, engine='xlsxwriter'),
        file_name="historial_filtrado.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

    st.markdown("---")
    st.subheader("Descargar archivos originales:")

    for tipo, path in CARPETAS.items():
        archivos = glob(os.path.join(path,"*.xlsx"))
        if archivos:
            with st.expander(f"{tipo} ({len(archivos)} archivos)"):
                for archivo in archivos:
                    with open(archivo, "rb") as f:
                        st.download_button(
                            label=os.path.basename(archivo),
                            data=f,
                            file_name=os.path.basename(archivo),
                            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                        )

                        