import datetime
import streamlit as st
import plotly.express as px
from auth.auth import require_login
from database.db import init_db
from utils.branding import set_branding
from utils.formatting import formatear_columnas
from utils.exporting import mostrar_grafico_con_descargas, botones_descarga_tabla
from utils.queries import get_inspecciones_full
from utils.kpis import (
    kpi_total, kpi_archivo, kpi_derivadas, kpi_cuentas_recurrentes,
    kpi_rendimiento_por_inspector, kpi_rendimiento_por_analista,
    kpi_conteo_por_detalle, kpi_pivot_area_detalle_jerarquico,
    kpi_crecimiento_por_rango_orden, kpi_top_sectores, agregar_porcentaje,
    columna_orden_numerica,
)

st.set_page_config(page_title="Dashboard de Indicadores", page_icon="📊", layout="wide")
set_branding()
init_db()
require_login()

st.title("📊 Indicador Unidad de Reclamos")

# ---------- Filtro de periodo (fechas) ----------
col_f1, col_f2, col_f3 = st.columns([1, 1, 2])
with col_f1:
    fecha_inicio = st.date_input("Desde", value=datetime.date.today().replace(day=1))
with col_f2:
    fecha_fin = st.date_input("Hasta", value=datetime.date.today())
with col_f3:
    st.write("")
    st.write("")
    st.caption("El dashboard se recalcula automáticamente según el rango seleccionado.")

df = get_inspecciones_full(fecha_inicio.isoformat(), fecha_fin.isoformat())

if df.empty:
    st.info("No hay inspecciones registradas en el periodo seleccionado.")
    st.stop()

# ---------- Filtro global adicional e independiente: rango de Número de orden ----------
st.caption("Filtro adicional (independiente del rango de fechas) por rango de Número de orden:")
orden_num_serie = columna_orden_numerica(df)
orden_min_disponible = int(orden_num_serie.min()) if not orden_num_serie.empty else 0
orden_max_disponible = int(orden_num_serie.max()) if not orden_num_serie.empty else 0

col_o1, col_o2 = st.columns(2)
with col_o1:
    orden_inicial = st.number_input(
        "Orden Inicial", min_value=0, value=orden_min_disponible, step=1, key="orden_inicial_filtro"
    )
with col_o2:
    orden_final = st.number_input(
        "Orden Final", min_value=0, value=orden_max_disponible, step=1, key="orden_final_filtro"
    )

df = df[(orden_num_serie >= orden_inicial) & (orden_num_serie <= orden_final)]

if df.empty:
    st.warning("No hay inspecciones cuyo Número de orden esté dentro de ese rango.")
    st.stop()

st.divider()

# =========================================================
# 1. TARJETAS SUPERIORES CLICABLES (con % sobre el total del periodo)
# =========================================================
st.subheader("Indicadores del periodo")
st.caption("Haz clic en un indicador para filtrar todo el dashboard por esa categoría.")

if "kpi_filtro" not in st.session_state:
    st.session_state["kpi_filtro"] = "Total"

total_periodo = kpi_total(df)
archivo_n = kpi_archivo(df)
derivadas_n = kpi_derivadas(df)


def _pct(n):
    return round(n / total_periodo * 100, 1) if total_periodo else 0.0


opciones_kpi = [
    ("Total de Inspecciones", "Total", total_periodo, 100.0),
    ("Archivo", "Archivo", archivo_n, _pct(archivo_n)),
    ("Derivadas", "Derivadas", derivadas_n, _pct(derivadas_n)),
]

cols_kpi = st.columns(3)
for col, (etiqueta, valor_kpi, cantidad, pct) in zip(cols_kpi, opciones_kpi):
    activo = st.session_state["kpi_filtro"] == valor_kpi
    if col.button(
        f"{etiqueta} — {cantidad} ({pct}%)",
        key=f"kpi_btn_{valor_kpi}",
        use_container_width=True,
        type="primary" if activo else "secondary",
    ):
        st.session_state["kpi_filtro"] = valor_kpi
        st.rerun()

filtro = st.session_state["kpi_filtro"]


def aplicar_filtro_kpi(data):
    """Filtra cualquier DataFrame de inspecciones según el KPI activo."""
    if filtro == "Archivo":
        return data[data["area_destino"] == "ARCHIVO"]
    if filtro == "Derivadas":
        return data[data["area_destino"] != "ARCHIVO"]
    return data


df_f = aplicar_filtro_kpi(df)
total_visible = len(df_f)  # denominador de "Porcentaje" para el resto del dashboard

if filtro != "Total":
    st.info(f"Mostrando el dashboard filtrado por: **{filtro}** ({total_visible} inspecciones)")

if df_f.empty:
    st.warning("No hay inspecciones para este filtro en el periodo seleccionado.")
    st.stop()

st.divider()

# =========================================================
# 2. Cantidad de ODS por Detalle — gráfico con % + descargas
# =========================================================
st.subheader("📋 Cantidad de ODS por Detalle")
conteo_detalle = agregar_porcentaje(kpi_conteo_por_detalle(df_f), "total", total=total_visible)
conteo_detalle["etiqueta"] = conteo_detalle.apply(lambda r: f"{r['total']} ({r['Porcentaje']}%)", axis=1)

fig_detalle = px.bar(
    conteo_detalle, x="total", y="detalle", orientation="h",
    text="etiqueta", color="total", color_continuous_scale="Blues",
    custom_data=["Porcentaje"],
)
fig_detalle.update_layout(showlegend=False, coloraxis_showscale=False,
                           yaxis_title="", xaxis_title="Cantidad",
                           yaxis={"categoryorder": "total ascending"})
fig_detalle.update_traces(
    hovertemplate="Detalle: %{y}<br>Cantidad: %{x}<br>Porcentaje: %{customdata[0]}%<extra></extra>"
)
mostrar_grafico_con_descargas(fig_detalle, "ods_por_detalle", key="detalle")

st.divider()

# =========================================================
# 3. Tabla dinámica jerárquica: Área destino → Detalle (con color + % + descargas)
# =========================================================
st.subheader("🧮 Tabla dinámica: Área destino → Detalle")
st.caption(
    "El Área destino aparece una sola vez como agrupador (azul oscuro), con los "
    "Detalles indentados debajo (celeste claro). El Porcentaje se calcula sobre "
    "el total de órdenes visibles en este momento."
)
tabla_jer_cruda = agregar_porcentaje(kpi_pivot_area_detalle_jerarquico(df_f), "Cantidad", total=total_visible)

if tabla_jer_cruda.empty:
    st.info("No hay datos para mostrar en la tabla dinámica.")
else:
    tabla_jer_cruda["Porcentaje"] = tabla_jer_cruda["Porcentaje"].map(lambda v: f"{v:.1f}%")
    tabla_jerarquica = formatear_columnas(tabla_jer_cruda)
    col_principal = tabla_jerarquica.columns[0]  # "Área Destino / Detalle"

    def _resaltar_jerarquia(fila):
        es_area = not str(fila[col_principal]).lstrip().startswith("↳")
        if es_area:
            estilo = "background-color: #0D47A1; color: #FFFFFF; font-weight: bold;"
        else:
            estilo = "background-color: #BBDEFB; color: #0D47A1;"
        return [estilo] * len(fila)

    tabla_estilizada = tabla_jerarquica.style.apply(_resaltar_jerarquia, axis=1)
    st.dataframe(tabla_estilizada, use_container_width=False, hide_index=True)
    botones_descarga_tabla(tabla_jerarquica, "tabla_area_detalle",
                            "Tabla dinámica: Área destino - Detalle", key="area_detalle")

st.divider()

# =========================================================
# 4. Crecimiento / decrecimiento entre dos bloques de Número de orden (SIN Porcentaje, por excepción)
# =========================================================
st.subheader("📈 Crecimiento y decrecimiento por Área destino")
st.caption(
    "Compara dos bloques de Número de orden (por ejemplo, órdenes 1 a 100 contra "
    "101 a 200). Esta sección usa el histórico completo, independiente de los "
    "filtros de fecha y de Número de orden de arriba (pero respeta el indicador "
    "elegido en las tarjetas). Nota: esta tabla no lleva columna de Porcentaje, "
    "ya que su naturaleza es comparar dos bloques entre sí."
)

df_historico = aplicar_filtro_kpi(get_inspecciones_full())  # histórico completo + filtro de indicador
orden_num_hist = columna_orden_numerica(df_historico)
orden_min_hist = int(orden_num_hist.min()) if not orden_num_hist.empty else 0
orden_max_hist = int(orden_num_hist.max()) if not orden_num_hist.empty else 0
punto_medio = (
    orden_min_hist + (orden_max_hist - orden_min_hist) // 2
    if orden_max_hist > orden_min_hist else orden_min_hist
)

st.markdown("**Rango A**")
col_a1, col_a2 = st.columns(2)
with col_a1:
    orden_ini_a = st.number_input(
        "Rango A: Orden Inicial", min_value=0, value=orden_min_hist, step=1, key="orden_ini_a"
    )
with col_a2:
    orden_fin_a = st.number_input(
        "Rango A: Orden Final", min_value=0, value=punto_medio, step=1, key="orden_fin_a"
    )

st.markdown("**Rango B**")
col_b1, col_b2 = st.columns(2)
with col_b1:
    orden_ini_b = st.number_input(
        "Rango B: Orden Inicial", min_value=0, value=punto_medio + 1, step=1, key="orden_ini_b"
    )
with col_b2:
    orden_fin_b = st.number_input(
        "Rango B: Orden Final", min_value=0, value=orden_max_hist, step=1, key="orden_fin_b"
    )

label_a = f"A: Órdenes {orden_ini_a}-{orden_fin_a}"
label_b = f"B: Órdenes {orden_ini_b}-{orden_fin_b}"

tabla_crecimiento_cruda = kpi_crecimiento_por_rango_orden(
    df_historico, orden_ini_a, orden_fin_a, orden_ini_b, orden_fin_b, label_a, label_b
)

if tabla_crecimiento_cruda.empty:
    st.info("No hay inspecciones en ninguno de los dos rangos de orden seleccionados.")
else:
    tabla_crecimiento = formatear_columnas(tabla_crecimiento_cruda)
    st.dataframe(
        tabla_crecimiento,
        use_container_width=False,
        hide_index=True,
        column_config={
            "Crecimiento %": st.column_config.NumberColumn("Crecimiento %", format="%.1f%%"),
        },
    )
    st.caption("Un valor 'inf' significa que el área no tuvo órdenes en el Rango A pero sí en el Rango B.")
    botones_descarga_tabla(tabla_crecimiento, "crecimiento_por_area",
                            "Crecimiento y decrecimiento por Área destino", key="crecimiento")

st.divider()

# =========================================================
# 4.1 Sectores con más inspecciones — TABLA (Sector, Lugar, Cantidad, Porcentaje)
# =========================================================
st.subheader("📍 Sectores con más inspecciones")
tabla_sectores_cruda = agregar_porcentaje(kpi_top_sectores(df_f, top_n=10), "total", total=total_visible)

if tabla_sectores_cruda.empty:
    st.info("No hay datos de sectores para este filtro.")
else:
    tabla_sectores_cruda["Porcentaje"] = tabla_sectores_cruda["Porcentaje"].map(lambda v: f"{v:.1f}%")
    tabla_sectores = tabla_sectores_cruda.rename(
        columns={"sector": "Sector", "lugar": "Lugar", "total": "Cantidad"}
    )
    st.dataframe(tabla_sectores, use_container_width=False, hide_index=True)
    botones_descarga_tabla(tabla_sectores, "sectores_top", "Sectores con más inspecciones", key="sectores")

st.divider()

# =========================================================
# 5. Rendimiento por Inspectores y por Analista — gráficos con % + descargas
# =========================================================
col_a, col_b = st.columns(2)

with col_a:
    st.subheader("👷 Rendimiento por Inspector")
    rank_insp = agregar_porcentaje(kpi_rendimiento_por_inspector(df_f), "total_ordenes", total=total_visible)
    rank_insp["etiqueta"] = rank_insp.apply(lambda r: f"{r['total_ordenes']} ({r['Porcentaje']}%)", axis=1)
    fig_insp = px.bar(rank_insp, x="inspector", y="total_ordenes", text="etiqueta",
                       color="total_ordenes", color_continuous_scale="Greens",
                       custom_data=["Porcentaje"])
    fig_insp.update_layout(showlegend=False, coloraxis_showscale=False,
                            xaxis_title="", yaxis_title="Órdenes atendidas")
    fig_insp.update_traces(
        hovertemplate="Inspector: %{x}<br>Órdenes: %{y}<br>Porcentaje: %{customdata[0]}%<extra></extra>"
    )
    mostrar_grafico_con_descargas(fig_insp, "rendimiento_inspector", key="insp")
    if not rank_insp.empty:
        st.success(
            f"🏆 **Más órdenes:** {rank_insp.iloc[0]['inspector']} "
            f"({rank_insp.iloc[0]['total_ordenes']} órdenes, {rank_insp.iloc[0]['Porcentaje']}%)\n\n"
            f"🔻 **Menos órdenes:** {rank_insp.iloc[-1]['inspector']} "
            f"({rank_insp.iloc[-1]['total_ordenes']} órdenes, {rank_insp.iloc[-1]['Porcentaje']}%)"
        )

with col_b:
    st.subheader("🧑‍💼 Rendimiento por Analista")
    rank_analista = agregar_porcentaje(kpi_rendimiento_por_analista(df_f), "total_ordenes", total=total_visible)
    rank_analista["etiqueta"] = rank_analista.apply(lambda r: f"{r['total_ordenes']} ({r['Porcentaje']}%)", axis=1)
    fig_analista = px.bar(rank_analista, x="analista", y="total_ordenes", text="etiqueta",
                           color="total_ordenes", color_continuous_scale="Purples",
                           custom_data=["Porcentaje"])
    fig_analista.update_layout(showlegend=False, coloraxis_showscale=False,
                                xaxis_title="", yaxis_title="Órdenes atendidas")
    fig_analista.update_traces(
        hovertemplate="Analista: %{x}<br>Órdenes: %{y}<br>Porcentaje: %{customdata[0]}%<extra></extra>"
    )
    mostrar_grafico_con_descargas(fig_analista, "rendimiento_analista", key="analista")
    if not rank_analista.empty:
        st.success(
            f"🏆 **Más órdenes:** {rank_analista.iloc[0]['analista']} "
            f"({rank_analista.iloc[0]['total_ordenes']} órdenes, {rank_analista.iloc[0]['Porcentaje']}%)\n\n"
            f"🔻 **Menos órdenes:** {rank_analista.iloc[-1]['analista']} "
            f"({rank_analista.iloc[-1]['total_ordenes']} órdenes, {rank_analista.iloc[-1]['Porcentaje']}%)"
        )

st.divider()

# ---------- Cuentas recurrentes (con % + descargas) ----------
st.subheader("🔁 Cuentas recurrentes en el periodo")
recurrentes_cruda = kpi_cuentas_recurrentes(df_f)
if recurrentes_cruda.empty:
    st.success("No se detectaron cuentas repetidas en este periodo.")
else:
    recurrentes_cruda = agregar_porcentaje(recurrentes_cruda, "veces_ingresada", total=total_visible)
    recurrentes_cruda["Porcentaje"] = recurrentes_cruda["Porcentaje"].map(lambda v: f"{v:.1f}%")
    recurrentes = formatear_columnas(recurrentes_cruda)
    st.dataframe(recurrentes, use_container_width=False, hide_index=True)
    botones_descarga_tabla(recurrentes, "cuentas_recurrentes", "Cuentas recurrentes", key="recurrentes")

st.divider()

# ---------- Evolución diaria (con % + descargas) ----------
st.subheader("📅 Evolución diaria de inspecciones")
serie_diaria = agregar_porcentaje(
    df_f.groupby("fecha").size().reset_index(name="total"), "total", total=total_visible
)
fig3 = px.line(serie_diaria, x="fecha", y="total", markers=True, custom_data=["Porcentaje"])
fig3.update_traces(
    hovertemplate="Fecha: %{x}<br>Cantidad: %{y}<br>Porcentaje: %{customdata[0]}%<extra></extra>"
)
fig3.update_layout(xaxis_title="", yaxis_title="Cantidad de inspecciones")
mostrar_grafico_con_descargas(fig3, "evolucion_diaria", key="evolucion")

# ---------- Exportar datos crudos del periodo ----------
st.divider()
st.subheader("⬇️ Exportar datos crudos del periodo")
st.caption("Exporta el detalle completo de inspecciones del periodo y filtro actuales (no un resumen).")
csv = df_f.to_csv(index=False).encode("utf-8-sig")
st.download_button(
    "Descargar inspecciones del periodo (CSV)",
    data=csv,
    file_name=f"inspecciones_{fecha_inicio}_{fecha_fin}_{filtro}.csv",
    mime="text/csv",
)
