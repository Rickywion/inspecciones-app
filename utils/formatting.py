"""
Formato de presentación para tablas del dashboard: renombra columnas
técnicas (snake_case) a etiquetas formales antes de renderizar.
"""
import pandas as pd

# Mapeo explícito para las columnas técnicas más comunes del proyecto.
RENOMBRES = {
    "area_destino": "Área Destino",
    "detalle": "Detalle",
    "sector": "Sector",
    "lugar": "Lugar",
    "inspector": "Inspector",
    "analista": "Analista",
    "numero_cuenta": "Número de Cuenta",
    "numero_orden": "Número de Orden",
    "fecha": "Fecha",
    "total_ordenes": "Total Órdenes",
    "veces_ingresada": "Veces Ingresada",
    "total": "Total",
    "Área destino / Detalle": "Área Destino / Detalle",
}


def formatear_columnas(df: pd.DataFrame) -> pd.DataFrame:
    """
    Devuelve una copia del DataFrame con columnas renombradas para mostrar
    en pantalla: sin guiones bajos, con mayúscula inicial en cada palabra.

    Las columnas conocidas usan el texto exacto de RENOMBRES; cualquier
    columna no listada se formatea automáticamente (guion_bajo -> "Guion Bajo").
    """
    nuevas = {}
    for col in df.columns:
        if col in RENOMBRES:
            nuevas[col] = RENOMBRES[col]
        elif isinstance(col, str):
            nuevas[col] = col.replace("_", " ").strip().title()
        else:
            nuevas[col] = col
    return df.rename(columns=nuevas)
