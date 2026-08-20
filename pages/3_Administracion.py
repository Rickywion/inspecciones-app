import streamlit as st
from auth.auth import (
    require_login, is_admin, create_user, list_users,
    set_user_active, reset_password, contar_usuarios, MAX_USUARIOS,
)
from database.db import init_db
from utils.branding import set_branding

st.set_page_config(page_title="Administración", page_icon="⚙️", layout="wide")
set_branding()
init_db()
require_login()

st.title("⚙️ Administración de usuarios")

if not is_admin():
    st.error("Solo el rol administrador puede acceder a este módulo.")
    st.stop()

st.info(
    "Las listas desplegables (Área destino, Detalle, Sector, Inspector y "
    "Analista) **no se administran desde aquí**: son listas fijas definidas "
    "en el archivo `config/constants.py` para garantizar la integridad de "
    "los datos. Si necesitas agregar o corregir un valor, pide al "
    "desarrollador que edite ese archivo."
)

st.subheader("Crear nuevo usuario")
total_usuarios = contar_usuarios()
st.caption(f"Usuarios registrados: **{total_usuarios} / {MAX_USUARIOS}**")

if total_usuarios >= MAX_USUARIOS:
    st.warning(
        f"Se alcanzó el límite máximo de {MAX_USUARIOS} usuarios. "
        "Desactiva o elimina alguno para poder crear uno nuevo."
    )

with st.form("nuevo_usuario", clear_on_submit=True):
    c1, c2, c3 = st.columns(3)
    with c1:
        u_username = st.text_input("Usuario (login)")
    with c2:
        u_nombre = st.text_input("Nombre completo")
    with c3:
        u_rol = st.selectbox("Rol", ["operador", "administrador"])
    u_password = st.text_input("Contraseña temporal", type="password")

    if st.form_submit_button("Crear usuario"):
        if not u_username or not u_password or not u_nombre:
            st.error("Todos los campos son obligatorios.")
        else:
            ok, msg = create_user(u_username, u_password, u_nombre, u_rol)
            st.success(msg) if ok else st.error(msg)

st.divider()
st.subheader("Usuarios existentes")
users = list_users()
for u in users:
    c1, c2, c3, c4, c5 = st.columns([2, 2, 1.5, 1.5, 2])
    c1.write(f"**{u['username']}**")
    c2.write(u["nombre_completo"])
    c3.write(u["rol"])
    c4.write("✅ Activo" if u["activo"] else "🚫 Inactivo")
    with c5:
        if st.button("Activar/Desactivar", key=f"toggle_{u['id']}"):
            set_user_active(u["id"], not u["activo"])
            st.rerun()

st.divider()
st.subheader("Restablecer contraseña")
users_dict = {f"{u['username']} ({u['nombre_completo']})": u["id"] for u in users}
if users_dict:
    sel = st.selectbox("Selecciona usuario", options=list(users_dict.keys()))
    new_pass = st.text_input("Nueva contraseña", type="password", key="reset_pass")
    if st.button("Restablecer contraseña"):
        if new_pass:
            reset_password(users_dict[sel], new_pass)
            st.success("Contraseña actualizada.")
        else:
            st.error("Ingresa una contraseña.")
