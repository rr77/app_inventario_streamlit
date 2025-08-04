import streamlit as st
import pandas as pd
import os
from datetime import datetime
from utils.excel_tools import to_excel_bytes

CATALOGO_PATH = "catalogo/catalogo.xlsx"
ENTRADAS_FOLDER = "entradas/"

def save_entrada(df, fecha):
    """
    Guarda el DataFrame de entrada en la carpeta de entradas con formato: entradas_YYYY-MM-DD.xlsx
    Si ya existe, concatena la nueva entrada.
    """
    nombre_archivo = f"entradas_{fecha}.xlsx"
    path = os.path.join(ENTRADAS_FOLDER, nombre_archivo)
    if os.path.exists(path):
        df_old = pd.read_excel(path)
        df_new = pd.concat([df_old, df], ignore_index=True)
    else:
        df_new = df
    df_new.to_excel(path, index=False)

def show_latest_entradas():
    """Muestra las últimas 5 entradas cargadas (de los archivos más recientes)."""
    archivos = [f for f in os.listdir(ENTRADAS_FOLDER) if f.endswith('.xlsx')]
    archivos = sorted(archivos, reverse=True)
    dfs = []
    for archivo in archivos[:5]:
        try:
            df = pd.read_excel(os.path.join(ENTRADAS_FOLDER, archivo))
            df['Archivo'] = archivo
            dfs.append(df)
        except:
            pass
    if dfs:
        return pd.concat(dfs, ignore_index=True)
    else:
        return pd.DataFrame()

def entradas_module():
    st.title("Registro de Entradas a Inventario")
    st.info("""
    Aquí puedes registrar productos que ingresan al inventario.  
    Puedes hacerlo manualmente o cargando un archivo Excel.  
    Todos los registros quedan almacenados en la carpeta `/entradas/` para respaldo y auditoría.
    """)

    cat = pd.read_excel(CATALOGO_PATH)
    if cat.empty:
        st.warning("El catálogo está vacío. Debes cargar productos primero en el catálogo.")
        return
        
    fecha = st.date_input("Fecha de entrada", value=datetime.today())
    modo = st.radio("Forma de carga", ["Carga manual", "Desde archivo Excel"])

    if modo == "Carga manual":
        with st.form("form_entradas"):
            item = st.selectbox("Item", cat["Item"].unique())
            subcat = cat[cat["Item"] == item]["Subcategoría"].values[0]
            ubic = st.selectbox("Ubicación destino", ["Almacén", "Barra", "Vinera"])
            cantidad = st.number_input("Cantidad", min_value=0.01)
            submit = st.form_submit_button("Registrar entrada")
        if submit:
            nueva = pd.DataFrame([{
                "Fecha": fecha.strftime('%Y-%m-%d'),
                "Item": item,
                "Subcategoría": subcat,
                "Ubicación destino": ubic,
                "Cantidad": cantidad
            }])
            save_entrada(nueva, fecha.strftime("%Y-%m-%d"))
            st.success("Entrada registrada correctamente.")

    else:
        st.write(
            "El archivo Excel debe tener las columnas: Fecha, Item, Subcategoría, Ubicación destino, Cantidad")
        archivo = st.file_uploader("Selecciona el archivo Excel...", type=["xlsx"])
        if archivo:
            try:
                df = pd.read_excel(archivo)
                st.dataframe(df)
                if st.button("Procesar archivo y registrar entradas"):
                    save_entrada(df, fecha.strftime("%Y-%m-%d"))
                    st.success("Archivo de entradas procesado y guardado correctamente.")
            except Exception as e:
                st.error(f"Error leyendo Excel: {str(e)}")
    # Muestra últimas entradas para consulta rápida
    st.markdown("---")
    st.subheader("Últimas entradas registradas")
    df_hist = show_latest_entradas()
    if not df_hist.empty:
        st.dataframe(df_hist)
        st.download_button(
            label="Descargar últimas entradas (Excel)",
            data=to_excel_bytes(df_hist),
            file_name="ultimas_entradas.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
    else:
        st.info("No hay entradas registradas todavía.")