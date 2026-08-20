import datetime
import io
import pandas as pd
import streamlit as st

from auth.auth import require_login
from database.db import init_db
from utils.branding import set_branding
from config.constants import (
    AREAS_DESTINO, INSPECTORES, ANALISTAS, SECTORES,
    lugar_for_sector, detalles_for_area, IMPORT_REQUIRED_COLUMNS,
)
from utils.queries import (
    insert_inspeccion, account_exists_recently, order_exists, import_bulk_dataframe,
)

st.set_page_config(page_title="Formulario de Inspecciones", page_icon="📋", layout="wide")
set_branding()
init_db()
require_login()

st.title("📝 Registro de Inspección")
st.caption(f"Sesión: **{st.session_state['auth_nombre']}**")

# =========================================================
# No usamos st.form aquí a propósito. st.form "congela" los widgets hasta
# que se presiona el botón de envío, lo cual impediría que "Lugar"
# reaccione al cambiar "Sector", y que "Detalle" reaccione al cambiar
# "Área destino". Por eso son widgets normales + un botón "Guardar" manual.
# =========================================================

st.subheader("Ingreso diario")

# ---- Fila 1 ----
c1, c2, c3, c4 = st.columns(4)
with c1:
    fecha = st.date_input("Fecha *", value=datetime.date.today())
with c2:
    numero_cuenta = st.text_input("Número de cuenta *", help="Solo dígitos.")
with c3:
    numero_orden = st.text_input("Número de orden *", help="Alfanumérico, único.")
with c4:
    area_destino = st.selectbox("Área destino *", options=AREAS_DESTINO)

# ---- Fila 2 ----
opciones_detalle = detalles_for_area(area_destino)
c5, c6, c7 = st.columns(3)
with c5:
    detalle = st.selectbox("Detalle *", options=opciones_detalle,
                            help="Las opciones dependen del Área destino elegida.")
with c6:
    sector = st.selectbox("Sector *", options=SECTORES)
with c7:
    lugar = lugar_for_sector(sector)
    st.text_input("Lugar (automático)", value=lugar, disabled=True)

# ---- Fila 3 ----
c8, c9 = st.columns(2)
with c8:
    inspector = st.selectbox("Inspector *", options=INSPECTORES)
with c9:
    analista = st.selectbox("Analista *", options=ANALISTAS)

guardar = st.button("💾 Guardar inspección", type="primary", use_container_width=True)

if guardar:
    errores = []
    if not numero_cuenta.strip():
        errores.append("El número de cuenta es obligatorio.")
    elif not numero_cuenta.strip().isdigit():
        errores.append("El número de cuenta debe contener solo dígitos.")

    if not numero_orden.strip():
        errores.append("El número de orden es obligatorio.")
    elif order_exists(numero_orden.strip()):
        errores.append(f"El número de orden '{numero_orden}' ya existe en el sistema.")

    if not opciones_detalle:
        errores.append("El Área destino seleccionada no tiene Detalles configurados.")

    if errores:
        for e in errores:
            st.error(e)
    else:
        veces_previas = account_exists_recently(numero_cuenta.strip())

        ok, msg = insert_inspeccion(
            fecha=fecha.isoformat(),
            numero_cuenta=numero_cuenta.strip(),
            numero_orden=numero_orden.strip(),
            area_destino=area_destino,
            detalle=detalle,
            sector=sector,
            inspector=inspector,
            analista=analista,
        )

        if ok:
            st.success(msg)
            if veces_previas > 0:
                st.warning(
                    f"⚠️ La cuenta **{numero_cuenta}** ya había sido ingresada "
                    f"{veces_previas} vez/veces anteriormente. Verifica que no sea un duplicado."
                )
            st.rerun()
        else:
            st.error(msg)

st.divider()

# =========================================================
# IMPORTACIÓN MASIVA
# =========================================================
st.subheader("📥 Importación masiva de registros históricos")
st.caption(
    "Sube un archivo Excel (.xlsx) o CSV con inspecciones ya registradas manualmente. "
    "La columna **Lugar** no se incluye: se calcula automáticamente a partir del Sector."
)

with st.expander("Ver formato de archivo requerido (encabezados obligatorios)"):
    ejemplo = pd.DataFrame([{
        "Fecha": "2026-08-19",
        "Numero_cuenta": "123456",
        "Numero_orden": "ORD-0001",
        "Area_destino": "RECLAMOS",
        "Detalle": "REGULACION",
        "Sector": "1-11",
        "Inspector": "ANGEL ZAMBRANO",
        "Analista": "GUICELA GAIBOR",
    }])
    st.dataframe(ejemplo, use_container_width=True, hide_index=True)
    st.markdown(
        f"**Columnas obligatorias (todas):** {', '.join(IMPORT_REQUIRED_COLUMNS)}\n\n"
        "Los valores de Área destino, Sector, Inspector y Analista deben coincidir "
        "**exactamente** con las listas del sistema. El valor de **Detalle** debe "
        "corresponder al Área destino indicada (ver diccionario del formulario); "
        "de lo contrario la fila se marcará como novedad."
    )

archivo = st.file_uploader("Selecciona el archivo (.xlsx o .csv)", type=["xlsx", "csv"])

if archivo is not None:
    try:
        if archivo.name.lower().endswith(".csv"):
            df_import = pd.read_csv(archivo)
        else:
            df_import = pd.read_excel(archivo)
    except Exception as e:
        st.error(f"No se pudo leer el archivo: {e}")
        df_import = None

    if df_import is not None:
        faltantes = [c for c in IMPORT_REQUIRED_COLUMNS if c not in df_import.columns]
        if faltantes:
            st.error(f"Faltan columnas obligatorias en el archivo: {', '.join(faltantes)}")
        else:
            st.write(f"Se detectaron **{len(df_import)}** filas para importar. Vista previa:")
            st.dataframe(df_import.head(10), use_container_width=True, hide_index=True)

            if st.button("✅ Confirmar e integrar a la base de datos"):
                resumen, novedades = import_bulk_dataframe(df_import)

                total = len(resumen)
                ok_count = int((resumen["estado"] == "OK").sum()) if not resumen.empty else 0
                error_count = int((resumen["estado"] == "ERROR").sum()) if not resumen.empty else 0
                omit_count = int((resumen["estado"] == "OMITIDO").sum()) if not resumen.empty else 0

                st.success(f"Importación finalizada: {ok_count}/{total} filas cargadas correctamente.")

                if not novedades.empty:
                    st.warning(
                        f"{error_count} fila(s) con error y {omit_count} omitida(s) "
                        f"(duplicadas). Descarga el reporte para corregirlas."
                    )
                    st.dataframe(novedades, use_container_width=True, hide_index=True)

                    buffer = io.BytesIO()
                    with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
                        novedades.to_excel(writer, index=False, sheet_name="Novedades")
                    buffer.seek(0)

                    st.download_button(
                        "⬇️ Descargar reporte de novedades (Excel)",
                        data=buffer,
                        file_name="novedades_importacion.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    )
                else:
                    st.info("Todas las filas se importaron sin novedades. 🎉")
