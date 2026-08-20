"""
Migración v2 -> v3 de la base de datos.

Ejecutar UNA SOLA VEZ si ya tenías datos cargados con el esquema v2
(el que tenía autor_id, mal_generada, observaciones y analista_responsable
por separado).

Qué hace:
1. Respalda data/inspecciones.db a data/inspecciones_backup_v2.db
2. Copia las inspecciones antiguas a la nueva tabla:
   - analista_responsable -> analista
   - autor_id, mal_generada, observaciones: se descartan (ya no existen)
3. Deja la base de datos lista para trabajar con el nuevo esquema.

Uso:
    python database/migrate_v3.py
"""
import os
import shutil
import sqlite3

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(BASE_DIR, "data", "inspecciones.db")
BACKUP_PATH = os.path.join(BASE_DIR, "data", "inspecciones_backup_v2.db")
SCHEMA_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "schema.sql")


def main():
    if not os.path.exists(DB_PATH):
        print("No existe una base de datos previa. No hay nada que migrar.")
        print("Simplemente ejecuta la app: init_db() creará el esquema nuevo desde cero.")
        return

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    cols = [r[1] for r in cur.execute("PRAGMA table_info(inspecciones)").fetchall()]

    if "analista" in cols and "analista_responsable" not in cols:
        print("La base de datos ya está en el esquema v3. No se requiere migración.")
        conn.close()
        return

    if "analista_responsable" not in cols:
        print("No se reconoce el esquema de la base de datos existente (¿es v1?).")
        print("Ejecuta primero database/migrate_v2.py y luego este script.")
        conn.close()
        return

    print("Esquema v2 detectado. Iniciando migración a v3...")

    conn.close()
    shutil.copy2(DB_PATH, BACKUP_PATH)
    print(f"Respaldo creado en: {BACKUP_PATH}")

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    old_rows = cur.execute("""
        SELECT id, fecha, numero_cuenta, numero_orden, area_destino, detalle,
               sector, lugar, inspector, analista_responsable, created_at
        FROM inspecciones
    """).fetchall()
    print(f"{len(old_rows)} inspecciones antiguas encontradas.")

    cur.execute("ALTER TABLE inspecciones RENAME TO inspecciones_old")
    with open(SCHEMA_PATH, "r", encoding="utf-8") as f:
        conn.executescript(f.read())
    conn.commit()

    migrados, con_error = 0, 0
    for r in old_rows:
        try:
            cur.execute("""
                INSERT INTO inspecciones
                    (id, fecha, numero_cuenta, numero_orden, area_destino, detalle,
                     sector, lugar, inspector, analista, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                r["id"], r["fecha"], r["numero_cuenta"], r["numero_orden"],
                r["area_destino"], r["detalle"], r["sector"], r["lugar"],
                r["inspector"], r["analista_responsable"], r["created_at"],
            ))
            migrados += 1
        except Exception as e:
            print(f"  ⚠️ Error migrando inspección id={r['id']}: {e}")
            con_error += 1

    conn.commit()

    cur.execute("DROP TABLE IF EXISTS inspecciones_old")
    conn.commit()
    conn.close()

    print(f"Migración completa: {migrados} inspecciones migradas, {con_error} con error.")
    print("Nota: verifica en 'Base Consolidada' que Área destino y Detalle sigan")
    print("siendo combinaciones válidas según el nuevo diccionario Área->Detalle.")


if __name__ == "__main__":
    main()
