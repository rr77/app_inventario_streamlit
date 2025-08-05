import pandas as pd


def to_ml(item: str, cantidad: float, catalogo: pd.DataFrame) -> float:
    """Convert `cantidad` to milliliters based on catalog info.

    If the item has "Tipo de unidad" == "ml" and "Cantidad por unidad" > 0,
    the input is assumed to be expressed in whole bottles and is converted to ml.
    Otherwise the quantity is returned unchanged.
    """
    if catalogo is None or catalogo.empty:
        return cantidad
    row = catalogo[catalogo["Item"] == item]
    if row.empty:
        return cantidad
    tipo = row.iloc[0].get("Tipo de unidad")
    capacidad = row.iloc[0].get("Cantidad por unidad")
    try:
        if tipo == "ml" and pd.notnull(capacidad) and float(capacidad) > 0:
            return float(cantidad) * float(capacidad)
    except Exception:
        pass
    return cantidad


def to_bottles(item: str, cantidad_ml: float, catalogo: pd.DataFrame):
    """Return the number of bottles represented by `cantidad_ml`.

    If the catalog registers the item in milliliters and has a valid
    "Cantidad por unidad", the value is converted and returned. In case the
    conversion cannot be performed, ``None`` is returned.
    """
    if catalogo is None or catalogo.empty:
        return None
    row = catalogo[catalogo["Item"] == item]
    if row.empty:
        return None
    tipo = row.iloc[0].get("Tipo de unidad")
    capacidad = row.iloc[0].get("Cantidad por unidad")
    try:
        if tipo == "ml" and pd.notnull(capacidad) and float(capacidad) > 0:
            return float(cantidad_ml) / float(capacidad)
    except Exception:
        pass
    return None
