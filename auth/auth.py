"""
Autenticación simple basada en sesión de Streamlit + bcrypt.
Suficiente y seguro para un equipo interno pequeño (hasta MAX_USUARIOS
personas), sin dependencias externas tipo OAuth que serían
sobre-ingeniería para este caso.
"""
import bcrypt
import streamlit as st
from database.db import get_connection

MAX_USUARIOS = 10


def hash_password(plain_password: str) -> str:
    return bcrypt.hashpw(plain_password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(plain_password: str, password_hash: str) -> bool:
    return bcrypt.checkpw(plain_password.encode("utf-8"), password_hash.encode("utf-8"))


def login(username: str, password: str) -> bool:
    conn = get_connection()
    user = conn.execute(
        "SELECT * FROM users WHERE username = ? AND activo = 1", (username,)
    ).fetchone()
    conn.close()

    if user and verify_password(password, user["password_hash"]):
        st.session_state["auth_user_id"] = user["id"]
        st.session_state["auth_username"] = user["username"]
        st.session_state["auth_nombre"] = user["nombre_completo"]
        st.session_state["auth_rol"] = user["rol"]
        return True
    return False


def logout():
    for key in ["auth_user_id", "auth_username", "auth_nombre", "auth_rol"]:
        st.session_state.pop(key, None)


def is_authenticated() -> bool:
    return "auth_user_id" in st.session_state


def is_admin() -> bool:
    return st.session_state.get("auth_rol") == "administrador"


def require_login():
    """Bloquea el acceso a una página si no hay sesión iniciada."""
    if not is_authenticated():
        st.warning("⚠️ Debes iniciar sesión para acceder a esta página.")
        st.stop()


def contar_usuarios() -> int:
    conn = get_connection()
    total = conn.execute("SELECT COUNT(*) FROM users").fetchone()[0]
    conn.close()
    return total


def create_user(username, password, nombre_completo, rol="operador"):
    conn = get_connection()
    try:
        total_actual = conn.execute("SELECT COUNT(*) FROM users").fetchone()[0]
        if total_actual >= MAX_USUARIOS:
            return False, (
                f"Se alcanzó el límite máximo de {MAX_USUARIOS} usuarios. "
                "Desactiva o elimina alguno antes de crear uno nuevo."
            )
        conn.execute(
            """INSERT INTO users (username, password_hash, nombre_completo, rol)
               VALUES (?, ?, ?, ?)""",
            (username, hash_password(password), nombre_completo, rol),
        )
        conn.commit()
        return True, "Usuario creado correctamente."
    except Exception as e:
        return False, f"Error: {e}"
    finally:
        conn.close()


def list_users():
    conn = get_connection()
    users = conn.execute(
        "SELECT id, username, nombre_completo, rol, activo FROM users ORDER BY id"
    ).fetchall()
    conn.close()
    return users


def set_user_active(user_id: int, activo: bool):
    conn = get_connection()
    conn.execute("UPDATE users SET activo = ? WHERE id = ?", (1 if activo else 0, user_id))
    conn.commit()
    conn.close()


def reset_password(user_id: int, new_password: str):
    conn = get_connection()
    conn.execute(
        "UPDATE users SET password_hash = ? WHERE id = ?",
        (hash_password(new_password), user_id),
    )
    conn.commit()
    conn.close()
