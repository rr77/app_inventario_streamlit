import pandas as pd


def to_ml(item: str, cantidad: float, catalogo: pd.DataFrame) -> float:
    """Convert ``cantidad`` to milliliters based on catalog info.

    El catálogo puede definir la capacidad de cada ítem ya sea usando las
    columnas antiguas (``Tipo de unidad`` y ``Cantidad por unidad``) o la
    estructura más reciente (``Unidad`` y ``Volumen_ml_por_unidad``).
    Si se encuentra una capacidad válida, se asume que ``cantidad`` está
    expresada en unidades de botella y se convierte a mililitros.
    """
    if catalogo is None or catalogo.empty:
        return cantidad
    row = catalogo[catalogo["Item"] == item]
    if row.empty:
        return cantidad
    capacidad = (
        row.iloc[0].get("Volumen_ml_por_unidad")
        or row.iloc[0].get("Cantidad por unidad")
    )
    try:
        if pd.notnull(capacidad) and float(capacidad) > 0:
            return float(cantidad) * float(capacidad)
    except Exception:
        pass
    return cantidad


def to_bottles(item: str, cantidad_ml: float, catalogo: pd.DataFrame):
    """Return the number of bottles represented by ``cantidad_ml``.

    Se busca la capacidad en mililitros de cada ítem en el catálogo. Para
    compatibilidad, se aceptan tanto las columnas antiguas (``Cantidad por
    unidad``) como la nomenclatura reciente (``Volumen_ml_por_unidad``). Si no
    es posible realizar la conversión, se retorna ``None``.
    """
    if catalogo is None or catalogo.empty:
        return None
    row = catalogo[catalogo["Item"] == item]
    if row.empty:
        return None
    capacidad = (
        row.iloc[0].get("Volumen_ml_por_unidad")
        or row.iloc[0].get("Cantidad por unidad")
    )
    try:
        if pd.notnull(capacidad) and float(capacidad) > 0:
            return float(cantidad_ml) / float(capacidad)
    except Exception:
        pass
    return None
