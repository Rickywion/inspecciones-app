"""
Utilidades de descarga para el Dashboard.

- Tablas: botones de descarga en Excel (openpyxl, ya es dependencia del
  proyecto) y en PDF (requiere el paquete 'reportlab').
- Gráficos: el toolbar nativo de Plotly queda configurado para descargar
  en JPG con un clic (no requiere nada adicional); además se agrega un
  botón para descargar en PDF (requiere el paquete 'kaleido', que renderiza
  la figura del lado del servidor).

Si 'reportlab' o 'kaleido' no están instalados, los botones de PDF
correspondientes muestran un aviso en vez de romper la página.
"""
import io
import pandas as pd
import streamlit as st


# ---------- Gráficos (Plotly) ----------

def config_grafico(nombre_archivo: str) -> dict:
    """
    Config del toolbar nativo de Plotly: el ícono de cámara 📷 (siempre
    visible, no requiere librerías extra) descarga la imagen en JPG.
    """
    return {
        "displaylogo": False,
        "toImageButtonOptions": {
            "format": "jpeg",
            "filename": nombre_archivo,
            "scale": 2,
        },
    }


def mostrar_grafico_con_descargas(fig, nombre_archivo: str, key: str,
                                   use_container_width: bool = True):
    """
    Muestra el gráfico y agrega la posibilidad de descargarlo:
    - JPG: ícono de cámara en el toolbar del propio gráfico (nativo).
    - PDF: botón aparte, generado en el servidor con 'kaleido'.
    """
    st.plotly_chart(fig, use_container_width=use_container_width,
                     config=config_grafico(nombre_archivo))
    try:
        pdf_bytes = fig.to_image(format="pdf")
        st.download_button(
            "📄 Descargar gráfico en PDF",
            data=pdf_bytes,
            file_name=f"{nombre_archivo}.pdf",
            mime="application/pdf",
            key=f"pdf_chart_{key}",
        )
    except Exception:
        st.caption(
            "ℹ️ Usa el ícono de cámara 📷 en la esquina superior del gráfico "
            "para descargarlo en JPG. Para habilitar también la descarga en "
            "PDF, instala el paquete `kaleido`: `pip install -U kaleido`."
        )


# ---------- Tablas ----------

def _tabla_a_excel_bytes(df: pd.DataFrame) -> bytes:
    buffer = io.BytesIO()
    with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name="Datos")
    return buffer.getvalue()


def _tabla_a_pdf_bytes(df: pd.DataFrame, titulo: str) -> bytes:
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import letter, landscape
    from reportlab.lib.styles import getSampleStyleSheet
    from reportlab.lib.units import cm
    from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer

    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer, pagesize=landscape(letter),
        leftMargin=1.5 * cm, rightMargin=1.5 * cm,
        topMargin=1.5 * cm, bottomMargin=1.5 * cm,
    )
    estilos = getSampleStyleSheet()
    elementos = [Paragraph(titulo, estilos["Heading2"]), Spacer(1, 12)]

    datos = [list(df.columns)] + df.astype(str).values.tolist()
    tabla = Table(datos, repeatRows=1)
    tabla.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#0D47A1")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 8),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#E3F2FD")]),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
    ]))
    elementos.append(tabla)
    doc.build(elementos)
    return buffer.getvalue()


def botones_descarga_tabla(df: pd.DataFrame, nombre_archivo: str, titulo: str, key: str):
    """
    Coloca, lado a lado, un botón de descarga en Excel y otro en PDF para
    una tabla ya formateada (columnas formales, valores tal como se ven
    en pantalla).
    """
    if df is None or df.empty:
        return

    col1, col2 = st.columns(2)
    with col1:
        st.download_button(
            "📊 Descargar en Excel",
            data=_tabla_a_excel_bytes(df),
            file_name=f"{nombre_archivo}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            key=f"xlsx_{key}",
        )
    with col2:
        try:
            pdf_bytes = _tabla_a_pdf_bytes(df, titulo)
            st.download_button(
                "📄 Descargar en PDF",
                data=pdf_bytes,
                file_name=f"{nombre_archivo}.pdf",
                mime="application/pdf",
                key=f"pdf_table_{key}",
            )
        except ImportError:
            st.caption(
                "ℹ️ Para descargar esta tabla en PDF instala el paquete "
                "`reportlab`: `pip install reportlab`."
            )
        except Exception as e:
            st.caption(f"⚠️ No se pudo generar el PDF: {e}")
