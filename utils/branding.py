"""
Branding corporativo compartido por todas las páginas.

Llamar a set_branding() justo después de st.set_page_config() en cada
página. El logo se lee de un archivo LOCAL: assets/logo.png (debes
colocar tu imagen ahí; no se descarga nada de internet).
"""
import os
import streamlit as st

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LOGO_PATH = os.path.join(BASE_DIR, "assets", "logo.png")


def set_branding():
    if not os.path.exists(LOGO_PATH):
        return  # aún no se colocó assets/logo.png — la app sigue funcionando sin logo

    try:
        # st.logo() coloca la imagen arriba de la navegación del sidebar,
        # y acepta una ruta local directamente (no requiere URL).
        st.logo(LOGO_PATH)
    except Exception:
        # Respaldo para versiones de Streamlit anteriores a la 1.31, que
        # no tienen st.logo(). st.image() sí existe siempre, pero coloca
        # el logo DEBAJO de la lista de páginas (Streamlit dibuja esa
        # lista automáticamente antes de que corra el resto del script;
        # solo st.logo() puede colocar algo por encima de ella).
        try:
            st.sidebar.image(LOGO_PATH, width=150)
        except Exception:
            pass
