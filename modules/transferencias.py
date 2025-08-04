import streamlit as st
import pandas as pd
import os

TRANSFERENCIAS_FOLDER = "transferencias/"

def load_all_transferencias():
    """Carga y concatena todas las transferencias registradas (manuales y automáticas)."""
    archivos = [f for f in os.listdir(TRANSFERENCIAS_FOLDER) if f.endswith('.xlsx')]
    dfs = []
    for f in archivos:
        try:
            df = pd.read_excel(os.path.join(TRANSFERENCIAS_FOLDER, f))
            df['OrigenArchivo'] = f
            dfs.append(df)
        except Exception as e:
            st.warning(f"Error leyendo {f}: {e}")
    if dfs:
        df_tot = pd.concat(dfs, ignore_index=True)
        return df_tot
    else:
        return pd.DataFrame(columns=["Fecha","Item","Desde","Hacia","Cantidad","OrigenArchivo"])

def transferencias_module():
    st.title("Historial de Transferencias Internas")
    st.info(
        "Consulte, filtre y descargue el historial consolidado de transferencias internas. "
        "Esto incluye movimientos registrados de forma manual y aquellos tomados de auditorías (campo 'Requisicion')."
    )
    df = load_all_transferencias()
    if df.empty:
        st.info("No hay transferencias internas registradas aún.")
        return

    # Filtros
    items = list(df['Item'].unique())
    ubicaciones = list(df['Desde'].unique()) + list(df['Hacia'].unique())
    ubicaciones = list(sorted(set([u for u in ubicaciones if pd.notnull(u)])))

    col1, col2, col3 = st.columns(3)
    filtro_item = col1.selectbox("Filtrar por Item", ["Todos"] + items)
    filtro_desde = col2.selectbox("Filtrar por Origen", ["Todos"] + ubicaciones)
    filtro_hacia = col3.selectbox("Filtrar por Destino", ["Todos"] + ubicaciones)

    filtro_df = df.copy()
    if filtro_item != "Todos":
        filtro_df = filtro_df[filtro_df["Item"] == filtro_item]
    if filtro_desde != "Todos":
        filtro_df = filtro_df[filtro_df["Desde"] == filtro_desde]
    if filtro_hacia != "Todos":
        filtro_df = filtro_df[filtro_df["Hacia"] == filtro_hacia]

    st.dataframe(filtro_df, use_container_width=True)

    st.download_button(
        label="Descargar transferencias filtradas (Excel)",
        data=filtro_df.to_excel(index=False, engine='xlsxwriter'),
        file_name="transferencias_filtradas.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )