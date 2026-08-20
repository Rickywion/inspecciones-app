import pandas as pd
import streamlit as st
from auth.auth import require_login, is_admin
from database.db import init_db
from utils.branding import set_branding
from utils.queries import get_inspecciones_full, update_inspeccion, delete_inspeccion, validar_fila
from config.constants import AREAS_DESTINO, ALL_DETALLES, SECTORES, INSPECTORES, ANALISTAS

st.set_page_config(page_title="Base Consolidada", page_icon="🗄️", layout="wide")
set_branding()
init_db()
require_login()

st.title("🗄️ Base Consolidada")

# --- Control de acceso: SOLO administrador ---
if not is_admin():
    st.error("🔒 Acceso restringido: esta pestaña es exclusiva para usuarios con rol Administrador.")
    st.stop()

st.caption(
    "Edita celdas directamente en la tabla, o selecciona filas y pulsa el ícono de "
    "papelera para eliminarlas. Los cambios NO son permanentes hasta que presiones "
    "**Guardar cambios**."
)
st.info(
    "El desplegable de **Detalle** aquí muestra todos los valores posibles "
    "(no se filtra por Área destino como en el formulario). Al guardar se "
    "valida que la combinación Área destino + Detalle sea correcta; si no lo "
    "es, esa fila específica no se guardará y se te avisará el motivo.",
    icon="ℹ️",
)

df = get_inspecciones_full()

if df.empty:
    st.info("Todavía no hay inspecciones registradas.")
    st.stop()

# Guardamos una copia del estado original para poder comparar qué cambió
if "base_original" not in st.session_state or st.session_state.get("base_original_len") != len(df):
    st.session_state["base_original"] = df.copy()
    st.session_state["base_original_len"] = len(df)

columnas_editables = [
    "id", "fecha", "numero_cuenta", "numero_orden", "area_destino", "detalle",
    "sector", "lugar", "inspector", "analista",
]

edited_df = st.data_editor(
    df[columnas_editables],
    key="editor_base_consolidada",
    use_container_width=True,
    hide_index=True,
    num_rows="dynamic",  # permite eliminar filas (y agregar filas nuevas, opcional)
    column_config={
        "id": st.column_config.NumberColumn("ID", disabled=True),
        "lugar": st.column_config.TextColumn(
            "Lugar", disabled=True,
            help="Se recalcula automáticamente al guardar, según el Sector elegido.",
        ),
        "fecha": st.column_config.TextColumn("Fecha (YYYY-MM-DD)"),
        "area_destino": st.column_config.SelectboxColumn("Área destino", options=AREAS_DESTINO),
        "detalle": st.column_config.SelectboxColumn("Detalle", options=ALL_DETALLES),
        "sector": st.column_config.SelectboxColumn("Sector", options=SECTORES),
        "inspector": st.column_config.SelectboxColumn("Inspector", options=INSPECTORES),
        "analista": st.column_config.SelectboxColumn("Analista", options=ANALISTAS),
    },
)

if st.button("💾 Guardar cambios en la base de datos", type="primary"):
    original_ids = set(st.session_state["base_original"]["id"].tolist())
    edited_ids = set(edited_df["id"].dropna().astype(int).tolist())

    eliminados = original_ids - edited_ids
    errores, actualizados = [], 0

    # 1. Eliminar filas que ya no están en la tabla editada
    for insp_id in eliminados:
        delete_inspeccion(int(insp_id))

    # 2. Actualizar filas existentes (recalculando Lugar según Sector, y
    #    validando que Área destino + Detalle sean una combinación válida)
    for _, row in edited_df.iterrows():
        if pd.isna(row["id"]):
            continue  # fila nueva sin guardar aún — se ignora por simplicidad
        insp_id = int(row["id"])

        errores_fila = validar_fila(
            row["area_destino"], row["detalle"], row["sector"],
            row["inspector"], row["analista"],
        )
        if errores_fila:
            errores.append(f"Fila id={insp_id}: {' | '.join(errores_fila)}")
            continue

        ok, msg = update_inspeccion(
            insp_id=insp_id,
            fecha=str(row["fecha"]),
            numero_cuenta=str(row["numero_cuenta"]),
            numero_orden=str(row["numero_orden"]),
            area_destino=row["area_destino"],
            detalle=row["detalle"],
            sector=row["sector"],
            inspector=row["inspector"],
            analista=row["analista"],
        )
        if ok:
            actualizados += 1
        else:
            errores.append(f"Fila id={insp_id}: {msg}")

    st.success(f"Guardado: {actualizados} fila(s) actualizada(s), {len(eliminados)} eliminada(s).")
    if errores:
        st.error("Algunas filas no se pudieron guardar:")
        for e in errores:
            st.write(f"- {e}")

    # Limpiar estado para forzar recarga fresca de la tabla
    del st.session_state["base_original"]
    del st.session_state["base_original_len"]
    st.rerun()

st.divider()
st.subheader("⬇️ Exportar base completa")
csv = df.to_csv(index=False).encode("utf-8-sig")
st.download_button(
    "Descargar base consolidada (CSV)",
    data=csv,
    file_name="base_consolidada.csv",
    mime="text/csv",
)
