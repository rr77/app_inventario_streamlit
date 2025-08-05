import streamlit as st
from modules.catalogo import catalogo_module
from modules.recetas import recetas_module
from modules.stock import stock_module
from modules.entradas import entradas_module
from modules.transferencias import transferencias_module
from modules.ventas import ventas_module
from modules.auditorias import auditoria_apertura, auditoria_cierre
from modules.historial import historial_module
from modules.reportes import reportes_module

st.set_page_config(page_title="Gestión Inventario Licores", layout="wide")

# Barra lateral
st.sidebar.title("Menú")
opciones = [
    "Catálogo de Productos",
    "Recetas",
    "Stock",
    "Entradas",
    "Transferencias Internas",
    "Salidas (Ventas)",
    "Auditoría de Apertura",
    "Auditoría de Cierre",
    "Historial",
    "Reportes"
]
eleccion = st.sidebar.radio("Seleccione módulo:", opciones)

# Router de módulos
if eleccion == "Catálogo de Productos":
    catalogo_module()
elif eleccion == "Recetas":
    recetas_module()
elif eleccion == "Stock":
    stock_module()
elif eleccion == "Entradas":
    entradas_module()
elif eleccion == "Transferencias Internas":
    transferencias_module()
elif eleccion == "Salidas (Ventas)":
    ventas_module()
elif eleccion == "Auditoría de Apertura":
    auditoria_apertura()
elif eleccion == "Auditoría de Cierre":
    auditoria_cierre()
elif eleccion == "Historial":
    historial_module()
elif eleccion == "Reportes":
    reportes_module()
