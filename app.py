import streamlit as st
from database.db import init_db
from auth.auth import login, logout, is_authenticated
from utils.branding import set_branding

st.set_page_config(
    page_title="Gestión de Inspecciones",
    page_icon="📋",
    layout="wide",
)
set_branding()

# Inicializa la base de datos (crea tablas y datos semilla si es la primera vez)
init_db()

st.title("📋 Plataforma de Gestión de Inspecciones")

if not is_authenticated():
    st.subheader("Iniciar sesión")

    with st.form("login_form"):
        username = st.text_input("Usuario")
        password = st.text_input("Contraseña", type="password")
        submitted = st.form_submit_button("Ingresar")

        if submitted:
            if login(username, password):
                st.success("Sesión iniciada correctamente.")
                st.rerun()
            else:
                st.error("Usuario o contraseña incorrectos, o usuario inactivo.")

    st.info(
        "Usuario administrador inicial: **admin** / **admin123**\n\n"
        "⚠️ Cambia esta contraseña desde el módulo de Administración "
        "después del primer ingreso."
    )

else:
    st.success(f"Sesión activa: **{st.session_state['auth_nombre']}** "
               f"({st.session_state['auth_rol']})")
    st.write("Usa el menú lateral para ir al **Formulario** de captura o al **Dashboard** de indicadores.")

    if st.button("Cerrar sesión"):
        logout()
        st.rerun()
