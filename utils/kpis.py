"""
Cálculo de indicadores gerenciales (KPIs) a partir del DataFrame
consolidado de inspecciones (ver utils.queries.get_inspecciones_full).
"""
import pandas as pd


def agregar_porcentaje(df: pd.DataFrame, columna_valor: str, total: int = None,
                        nombre_columna: str = "Porcentaje") -> pd.DataFrame:
    """
    Agrega una columna de porcentaje calculada sobre 'total' (por ejemplo,
    el total de órdenes actualmente visibles en el dashboard). Si no se
    especifica 'total', se usa la suma de la propia columna_valor.
    """
    d = df.copy()
    denominador = total if total is not None else d[columna_valor].sum()
    if not denominador:
        d[nombre_columna] = 0.0
    else:
        d[nombre_columna] = (d[columna_valor] / denominador * 100).round(1)
    return d


def columna_orden_numerica(df: pd.DataFrame) -> pd.Series:
    """
    Convierte 'numero_orden' a numérico de forma segura para poder
    filtrar por rango (>= / <=): los valores que no son números (texto,
    vacíos, códigos alfanuméricos, etc.) se tratan como 0 en vez de
    hacer fallar la comparación.
    """
    return pd.to_numeric(df["numero_orden"], errors="coerce").fillna(0)


# ---------- Tarjetas superiores ----------

def kpi_total(df: pd.DataFrame) -> int:
    """Total de inspecciones (todas las órdenes)."""
    return int(len(df))


def kpi_archivo(df: pd.DataFrame) -> int:
    """Órdenes cuya Área destino es 'ARCHIVO'."""
    if df.empty:
        return 0
    return int((df["area_destino"] == "ARCHIVO").sum())


def kpi_derivadas(df: pd.DataFrame) -> int:
    """Derivadas = Total - Archivo."""
    return kpi_total(df) - kpi_archivo(df)


# ---------- Cuentas recurrentes ----------

def kpi_cuentas_recurrentes(df: pd.DataFrame) -> pd.DataFrame:
    """Cuentas que aparecen más de una vez en el periodo (posible duplicidad)."""
    if df.empty:
        return pd.DataFrame(columns=["numero_cuenta", "veces_ingresada"])

    d = df.copy()
    # Blindaje de formato: si alguna cuenta quedó guardada como '123456.0'
    # (dato legado, antes de corregir la importación masiva), se limpia
    # aquí también para que nunca se muestre con decimales.
    d["numero_cuenta"] = (
        d["numero_cuenta"].astype(str).str.strip()
        .str.replace(r"\.0$", "", regex=True)
    )

    conteo = (
        d.groupby("numero_cuenta")
        .size()
        .reset_index(name="veces_ingresada")
        .query("veces_ingresada > 1")
        .sort_values("veces_ingresada", ascending=False)
    )
    return conteo


# ---------- Rankings ----------

def kpi_rendimiento_por_inspector(df: pd.DataFrame) -> pd.DataFrame:
    """Ranking de órdenes atendidas por Inspector, de mayor a menor."""
    if df.empty:
        return pd.DataFrame(columns=["inspector", "total_ordenes"])
    return (
        df.groupby("inspector")
        .size()
        .reset_index(name="total_ordenes")
        .sort_values("total_ordenes", ascending=False)
    )


def kpi_rendimiento_por_analista(df: pd.DataFrame) -> pd.DataFrame:
    """Ranking de órdenes atendidas por Analista, de mayor a menor."""
    if df.empty:
        return pd.DataFrame(columns=["analista", "total_ordenes"])
    return (
        df.groupby("analista")
        .size()
        .reset_index(name="total_ordenes")
        .sort_values("total_ordenes", ascending=False)
    )


# ---------- Visualizaciones nuevas ----------

def kpi_conteo_por_detalle(df: pd.DataFrame) -> pd.DataFrame:
    """Cantidad de ODS (inspecciones) agrupadas por Detalle, de mayor a menor."""
    if df.empty:
        return pd.DataFrame(columns=["detalle", "total"])
    return (
        df.groupby("detalle")
        .size()
        .reset_index(name="total")
        .sort_values("total", ascending=False)
    )


def kpi_pivot_area_detalle(df: pd.DataFrame) -> pd.DataFrame:
    """
    Tabla: índice múltiple (Área destino, Detalle), con una única columna
    numérica 'Cantidad' = conteo de órdenes. Las combinaciones sin
    registros no aparecen (nunca hay filas en 0).
    """
    columnas_vacias = pd.DataFrame(columns=["area_destino", "detalle", "Cantidad"])
    if df.empty:
        return columnas_vacias.set_index(["area_destino", "detalle"])

    tabla = (
        df.dropna(subset=["area_destino", "detalle"])
        .groupby(["area_destino", "detalle"])
        .size()
        .reset_index(name="Cantidad")
    )
    tabla = tabla[tabla["Cantidad"] > 0]  # filtro explícito, aunque groupby ya no trae ceros
    tabla = tabla.sort_values(["area_destino", "Cantidad"], ascending=[True, False])
    tabla = tabla.set_index(["area_destino", "detalle"])
    return tabla


def kpi_pivot_area_detalle_jerarquico(df: pd.DataFrame) -> pd.DataFrame:
    """
    Versión "aplanada" de kpi_pivot_area_detalle pensada para mostrarse
    tal cual con st.dataframe, simulando la jerarquía visual de una tabla
    dinámica de Excel: el Área destino aparece UNA sola vez como
    encabezado de grupo (con el total de esa área), y los Detalles
    aparecen indentados justo debajo, con su propia cantidad.

    Devuelve columnas: 'Área destino / Detalle', 'Cantidad'.
    """
    base = kpi_pivot_area_detalle(df)
    if base.empty:
        return pd.DataFrame(columns=["Área destino / Detalle", "Cantidad"])

    filas = []
    for area in base.index.get_level_values("area_destino").unique():
        sub = base.loc[area]  # DataFrame indexado por 'detalle', columna 'Cantidad'
        total_area = int(sub["Cantidad"].sum())
        filas.append({"Área destino / Detalle": area, "Cantidad": total_area})
        for detalle, fila in sub.iterrows():
            filas.append({
                "Área destino / Detalle": f"\u00a0\u00a0\u00a0\u00a0↳ {detalle}",
                "Cantidad": int(fila["Cantidad"]),
            })

    return pd.DataFrame(filas)


def kpi_top_sectores(df: pd.DataFrame, top_n: int = 10) -> pd.DataFrame:
    """
    Top de sectores con más inspecciones. Devuelve 'sector' (código),
    'lugar' (nombre) y 'total' (cantidad de órdenes), listo para graficar.
    """
    if df.empty:
        return pd.DataFrame(columns=["sector", "lugar", "total"])
    tabla = (
        df.dropna(subset=["sector"])
        .groupby(["sector", "lugar"])
        .size()
        .reset_index(name="total")
        .sort_values("total", ascending=False)
        .head(top_n)
    )
    return tabla


def kpi_crecimiento_por_rango_orden(df: pd.DataFrame, orden_ini_a, orden_fin_a,
                                     orden_ini_b, orden_fin_b,
                                     label_a: str = "Rango A", label_b: str = "Rango B") -> pd.DataFrame:
    """
    Compara el total de órdenes por Área destino entre dos bloques de
    Número de orden elegidos manualmente por el usuario (en vez de
    fechas). Por ejemplo: órdenes 1-100 (Rango A) contra 101-200 (Rango B).

    Fuerza 'numero_orden' a numérico (no numérico -> 0, ver
    columna_orden_numerica) para que las comparaciones >= / <= nunca
    fallen ni excluyan por error todo el dataset si alguna orden quedó
    guardada como texto.
    """
    columnas_vacias = ["area_destino", label_a, label_b, "Crecimiento %"]
    if df.empty:
        return pd.DataFrame(columns=columnas_vacias)

    d = df.copy()
    d["orden_num"] = columna_orden_numerica(d)
    d = d.dropna(subset=["area_destino"])

    total_a = d[(d["orden_num"] >= orden_ini_a) & (d["orden_num"] <= orden_fin_a)].groupby("area_destino").size()
    total_b = d[(d["orden_num"] >= orden_ini_b) & (d["orden_num"] <= orden_fin_b)].groupby("area_destino").size()

    areas = sorted(set(total_a.index) | set(total_b.index))
    if not areas:
        return pd.DataFrame(columns=columnas_vacias)

    filas = []
    for area in areas:
        a = int(total_a.get(area, 0))
        b = int(total_b.get(area, 0))
        if a == 0:
            crecimiento = None if b == 0 else float("inf")
        else:
            crecimiento = round(((b - a) / a) * 100, 1)
        filas.append({"area_destino": area, label_a: a, label_b: b, "Crecimiento %": crecimiento})

    tabla = pd.DataFrame(filas).sort_values("Crecimiento %", ascending=False, na_position="last")
    return tabla
