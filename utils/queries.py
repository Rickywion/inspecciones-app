"""
Funciones de acceso a datos (CRUD) para inspecciones.
Centralizar aquí las queries facilita mantenimiento y una futura
migración de SQLite a PostgreSQL.
"""
import pandas as pd
from database.db import get_connection
from config.constants import (
    AREAS_DESTINO, INSPECTORES, ANALISTAS,
    SECTOR_LUGAR, lugar_for_sector, is_valid_area_detalle,
)


# ---------- Validación ----------

def limpiar_numero_cuenta(valor) -> str:
    """
    Normaliza un número de cuenta proveniente de Excel/CSV a texto entero
    limpio. Cuando una columna de Excel se infiere como numérica, pandas
    entrega valores float (ej. 123456.0) y str() los deja con el sufijo
    '.0' pegado — esta función lo elimina para que la cuenta se guarde
    y se muestre como '123456', no '123456.0'.
    """
    if valor is None:
        return ""
    if isinstance(valor, float):
        if pd.isna(valor):
            return ""
        return str(int(valor)) if valor.is_integer() else str(valor).strip()
    s = str(valor).strip()
    if s.endswith(".0") and s[:-2].isdigit():
        s = s[:-2]
    return s


def validar_fila(area_destino, detalle, sector, inspector, analista) -> list:
    """Devuelve una lista de errores (vacía si todo es válido)."""
    errores = []
    if area_destino not in AREAS_DESTINO:
        errores.append(f"Área destino inválida: '{area_destino}'")
    elif not is_valid_area_detalle(area_destino, detalle):
        errores.append(f"Detalle '{detalle}' no corresponde al Área destino '{area_destino}'")
    if sector not in SECTOR_LUGAR:
        errores.append(f"Sector inválido: '{sector}'")
    if inspector not in INSPECTORES:
        errores.append(f"Inspector inválido: '{inspector}'")
    if analista not in ANALISTAS:
        errores.append(f"Analista inválido: '{analista}'")
    return errores


# ---------- Inspecciones: lectura ----------

def account_exists_recently(numero_cuenta: str) -> int:
    """Cuenta cuántas veces ya se ha ingresado este número de cuenta (histórico)."""
    conn = get_connection()
    count = conn.execute(
        "SELECT COUNT(*) FROM inspecciones WHERE numero_cuenta = ?", (numero_cuenta,)
    ).fetchone()[0]
    conn.close()
    return count


def order_exists(numero_orden: str, exclude_id: int = None) -> bool:
    conn = get_connection()
    if exclude_id:
        count = conn.execute(
            "SELECT COUNT(*) FROM inspecciones WHERE numero_orden = ? AND id != ?",
            (numero_orden, exclude_id),
        ).fetchone()[0]
    else:
        count = conn.execute(
            "SELECT COUNT(*) FROM inspecciones WHERE numero_orden = ?", (numero_orden,)
        ).fetchone()[0]
    conn.close()
    return count > 0


def get_inspecciones_full(fecha_inicio=None, fecha_fin=None) -> pd.DataFrame:
    """Trae todas las inspecciones (para dashboard/exportar/Base Consolidada)."""
    conn = get_connection()
    query = """
        SELECT id, fecha, numero_cuenta, numero_orden, area_destino, detalle,
               sector, lugar, inspector, analista, created_at
        FROM inspecciones
        WHERE 1=1
    """
    params = []
    if fecha_inicio:
        query += " AND fecha >= ?"
        params.append(fecha_inicio)
    if fecha_fin:
        query += " AND fecha <= ?"
        params.append(fecha_fin)
    query += " ORDER BY fecha DESC, id DESC"

    df = pd.read_sql_query(query, conn, params=params)
    conn.close()
    return df


# ---------- Inspecciones: escritura ----------

def insert_inspeccion(fecha, numero_cuenta, numero_orden, area_destino, detalle,
                       sector, inspector, analista):
    errores = validar_fila(area_destino, detalle, sector, inspector, analista)
    if errores:
        return False, " | ".join(errores)

    lugar = lugar_for_sector(sector)
    conn = get_connection()
    try:
        conn.execute(
            """INSERT INTO inspecciones
               (fecha, numero_cuenta, numero_orden, area_destino, detalle,
                sector, lugar, inspector, analista)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (fecha, numero_cuenta, numero_orden, area_destino, detalle,
             sector, lugar, inspector, analista),
        )
        conn.commit()
        return True, "Inspección registrada correctamente."
    except Exception as e:
        return False, f"Error al guardar: {e}"
    finally:
        conn.close()


def update_inspeccion(insp_id, fecha, numero_cuenta, numero_orden, area_destino,
                       detalle, sector, inspector, analista):
    errores = validar_fila(area_destino, detalle, sector, inspector, analista)
    if errores:
        return False, " | ".join(errores)

    lugar = lugar_for_sector(sector)
    conn = get_connection()
    try:
        conn.execute(
            """UPDATE inspecciones SET
                   fecha=?, numero_cuenta=?, numero_orden=?, area_destino=?, detalle=?,
                   sector=?, lugar=?, inspector=?, analista=?, updated_at=datetime('now')
               WHERE id=?""",
            (fecha, numero_cuenta, numero_orden, area_destino, detalle,
             sector, lugar, inspector, analista, insp_id),
        )
        conn.commit()
        return True, "Actualizado."
    except Exception as e:
        return False, f"Error al actualizar: {e}"
    finally:
        conn.close()


def delete_inspeccion(insp_id):
    conn = get_connection()
    conn.execute("DELETE FROM inspecciones WHERE id = ?", (insp_id,))
    conn.commit()
    conn.close()


# ---------- Importación masiva ----------

def import_bulk_dataframe(df: pd.DataFrame) -> tuple:
    """
    Inserta en bloque las filas de un DataFrame (proveniente de un Excel/CSV subido).

    Devuelve una tupla (resumen_df, novedades_df):
      - resumen_df: una fila por cada registro del archivo, con su estado
        (OK / ERROR / OMITIDO) y el motivo.
      - novedades_df: SOLO las filas con problema (ERROR u OMITIDO), con
        los datos originales tal como vinieron en el archivo + el motivo,
        lista para exportarse a Excel y que el usuario las corrija.
    """
    resultados = []
    filas_novedad = []

    for idx, row in df.iterrows():
        fila_num = idx + 2  # +2: la fila 1 es el encabezado y pandas es 0-indexado
        fila_original = row.to_dict()

        def marcar_novedad(estado, motivo):
            resultados.append({"fila": fila_num, "estado": estado, "detalle": motivo})
            registro = dict(fila_original)
            registro["fila_excel"] = fila_num
            registro["motivo"] = motivo
            filas_novedad.append(registro)

        try:
            fecha = pd.to_datetime(row["Fecha"]).date().isoformat()
        except Exception:
            marcar_novedad("ERROR", f"Fecha inválida: '{row.get('Fecha')}'")
            continue

        numero_cuenta = limpiar_numero_cuenta(row.get("Numero_cuenta", ""))
        numero_orden = str(row.get("Numero_orden", "")).strip()
        area_destino = str(row.get("Area_destino", "")).strip().upper()
        detalle = str(row.get("Detalle", "")).strip().upper()
        sector = str(row.get("Sector", "")).strip()
        inspector = str(row.get("Inspector", "")).strip().upper()
        analista = str(row.get("Analista", "")).strip().upper()

        if not numero_cuenta or not numero_orden:
            marcar_novedad("ERROR", "Falta número de cuenta u orden.")
            continue

        if order_exists(numero_orden):
            marcar_novedad("OMITIDO", f"El número de orden '{numero_orden}' ya existe.")
            continue

        ok, msg = insert_inspeccion(
            fecha=fecha, numero_cuenta=numero_cuenta, numero_orden=numero_orden,
            area_destino=area_destino, detalle=detalle, sector=sector,
            inspector=inspector, analista=analista,
        )
        if ok:
            resultados.append({"fila": fila_num, "estado": "OK", "detalle": msg})
        else:
            marcar_novedad("ERROR", msg)

    resumen_df = pd.DataFrame(resultados)
    novedades_df = pd.DataFrame(filas_novedad)
    return resumen_df, novedades_df
