"""
Migración v1 -> v2 de la base de datos.

Ejecutar UNA SOLA VEZ si ya tenías datos cargados con la versión anterior
(la que usaba tablas de catálogo catalog_areas / catalog_detalle / etc.).

Qué hace:
1. Respalda data/inspecciones.db a data/inspecciones_backup_v1.db
2. Lee las inspecciones antiguas (con sus catálogos) y las vuelca a la
   nueva tabla inspecciones (con área/detalle/inspector como texto plano).
3. Deja la base de datos lista para trabajar con el nuevo esquema.

Uso:
    python database/migrate_v2.py
"""
import os
import shutil
import sqlite3
import sys

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(BASE_DIR, "data", "inspecciones.db")
BACKUP_PATH = os.path.join(BASE_DIR, "data", "inspecciones_backup_v1.db")
SCHEMA_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "schema.sql")


def main():
    if not os.path.exists(DB_PATH):
        print("No existe una base de datos previa. No hay nada que migrar.")
        print("Simplemente ejecuta la app: init_db() creará el esquema nuevo desde cero.")
        return

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    # ¿Ya está en formato nuevo? (columna area_destino existe en inspecciones)
    cols = [r[1] for r in cur.execute("PRAGMA table_info(inspecciones)").fetchall()]
    if "area_destino" in cols:
        print("La base de datos ya está en el esquema nuevo. No se requiere migración.")
        conn.close()
        return

    if "detalle_id" not in cols:
        print("No se reconoce el esquema de la base de datos existente. Migración abortada.")
        conn.close()
        return

    print("Esquema antiguo detectado. Iniciando migración...")

    # 1. Respaldo
    conn.close()
    shutil.copy2(DB_PATH, BACKUP_PATH)
    print(f"Respaldo creado en: {BACKUP_PATH}")

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    # 2. Leer inspecciones antiguas con sus catálogos resueltos a texto
    old_rows = cur.execute("""
        SELECT i.id, i.fecha, i.numero_cuenta, i.numero_orden,
               a.nombre AS area_destino, d.nombre AS detalle,
               insp.nombre AS inspector, i.autor_id,
               i.observaciones, i.created_at
        FROM inspecciones i
        LEFT JOIN catalog_areas a ON i.area_id = a.id
        LEFT JOIN catalog_detalle d ON i.detalle_id = d.id
        LEFT JOIN catalog_inspectores insp ON i.inspector_id = insp.id
    """).fetchall()
    print(f"{len(old_rows)} inspecciones antiguas encontradas.")

    # 3. Renombrar tabla vieja, crear esquema nuevo
    cur.execute("ALTER TABLE inspecciones RENAME TO inspecciones_old")
    with open(SCHEMA_PATH, "r", encoding="utf-8") as f:
        conn.executescript(f.read())
    conn.commit()

    # 4. Insertar datos migrados. Sector/Lugar/Analista responsable no existían
    #    antes, se dejan marcados como "SIN MIGRAR" para que el administrador
    #    los complete manualmente desde la pestaña Base Consolidada.
    migrados, con_error = 0, 0
    for r in old_rows:
        try:
            cur.execute("""
                INSERT INTO inspecciones
                    (id, fecha, numero_cuenta, numero_orden, area_destino, detalle,
                     sector, lugar, inspector, analista_responsable, mal_generada,
                     observaciones, autor_id, created_at)
                VALUES (?, ?, ?, ?, ?, ?, 'SIN MIGRAR', 'SIN MIGRAR', ?, 'SIN MIGRAR', 0, ?, ?, ?)
            """, (
                r["id"], r["fecha"], r["numero_cuenta"], r["numero_orden"],
                r["area_destino"] or "RECLAMOS", r["detalle"] or "DATOS CORRECTOS",
                r["inspector"] or "ANGEL ZAMBRANO",
                r["observaciones"], r["autor_id"], r["created_at"],
            ))
            migrados += 1
        except Exception as e:
            print(f"  ⚠️ Error migrando inspección id={r['id']}: {e}")
            con_error += 1

    conn.commit()

    # 5. Limpieza: eliminar tablas antiguas ya no usadas
    for tabla in ["inspecciones_old", "catalog_areas", "catalog_sectores",
                  "catalog_inspectores", "catalog_detalle"]:
        try:
            cur.execute(f"DROP TABLE IF EXISTS {tabla}")
        except Exception:
            pass
    conn.commit()
    conn.close()

    print(f"Migración completa: {migrados} inspecciones migradas, {con_error} con error.")
    print("IMPORTANTE: revisa en 'Base Consolidada' las filas con Sector/Lugar/")
    print("Analista responsable = 'SIN MIGRAR' y complétalas manualmente.")


if __name__ == "__main__":
    main()
