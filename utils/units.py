import pandas as pd


def _item_info(catalogo, item):
    info = catalogo[catalogo["Item"] == item]
    if info.empty:
        return None, None
    tipo = str(info.iloc[0]["Tipo de unidad"]).strip().lower()
    try:
        cantidad = float(info.iloc[0]["Cantidad por unidad"])
    except Exception:
        cantidad = None
    return tipo, cantidad

def to_ml(catalogo, item, cantidad):
    tipo, cant_unidad = _item_info(catalogo, item)
    if tipo is None or cant_unidad is None:
        return cantidad
    if tipo == "ml":
        return cantidad
    try:
        return cantidad * cant_unidad
    except Exception:
        return cantidad

def to_bottles(catalogo, item, cantidad_ml):
    tipo, cant_unidad = _item_info(catalogo, item)
    if tipo is None or cant_unidad in (None, 0):
        return 0
    try:
        return cantidad_ml / cant_unidad
    except Exception:
        return 0
