"""
Manejo de conexión e inicialización de la base de datos SQLite.
Para migrar a PostgreSQL en el futuro, solo hay que reemplazar
get_connection() por una conexión psycopg2/SQLAlchemy; el resto
del código (queries parametrizadas) es compatible en un 95%.
"""
import sqlite3
import os
import bcrypt

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(BASE_DIR, "data", "inspecciones.db")
SCHEMA_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "schema.sql")


def get_connection():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.execute("PRAGMA foreign_keys = ON;")
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    """Crea las tablas si no existen y siembra el usuario administrador inicial."""
    conn = get_connection()
    with open(SCHEMA_PATH, "r", encoding="utf-8") as f:
        conn.executescript(f.read())
    conn.commit()

    _seed_admin_user(conn)

    conn.close()


def _seed_admin_user(conn):
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM users")
    if cur.fetchone()[0] == 0:
        # Usuario administrador inicial. CAMBIAR LA CONTRASEÑA tras el primer login.
        pwd_hash = bcrypt.hashpw("admin123".encode("utf-8"), bcrypt.gensalt()).decode("utf-8")
        cur.execute(
            """INSERT INTO users (username, password_hash, nombre_completo, rol)
               VALUES (?, ?, ?, ?)""",
            ("admin", pwd_hash, "Administrador", "administrador"),
        )
        conn.commit()
