# Plataforma de Gestión de Inspecciones

Aplicación web interna para estandarizar la captura de inspecciones y calcular
indicadores gerenciales (KPIs) diarios y mensuales. Construida con **Streamlit**
+ **SQLite** + **pandas/Plotly**.

## Estructura del proyecto

```
inspecciones_app/
├── app.py                        # Login / entrada principal
├── requirements.txt
├── database/
│   ├── schema.sql                 # Definición de tablas
│   └── db.py                      # Conexión + inicialización + seed
├── auth/
│   └── auth.py                    # Login, sesiones, gestión de usuarios
├── pages/
│   ├── 1_Formulario.py            # Captura diaria + importación masiva
│   ├── 2_Dashboard.py             # KPIs e indicadores
│   ├── 3_Administracion.py        # Gestión de usuarios (solo admin)
│   └── 4_Base_Consolidada.py      # Ver/editar/eliminar todos los registros (solo admin)
├── config/
│   └── constants.py               # Listas fijas de los desplegables + diccionario Sector→Lugar
├── utils/
│   ├── queries.py                 # Acceso a datos (CRUD) + importación masiva
│   └── kpis.py                    # Cálculo de indicadores
└── data/
    └── inspecciones.db            # Base de datos (se crea automáticamente)
```

## 1. Requisitos previos

- Python 3.10 o superior instalado (verifica con `python --version`).
- No necesitas instalar ningún motor de base de datos aparte: SQLite viene incluido en Python.

## 2. Instalación

Abre una terminal en la carpeta del proyecto (`inspecciones_app`) y ejecuta:

```bash
# 1. Crear un entorno virtual (recomendado)
python -m venv .venv

# 2. Activar el entorno virtual
# En Windows:
.venv\Scripts\activate
# En Mac/Linux:
source .venv/bin/activate

# 3. Instalar dependencias
pip install -r requirements.txt
```

## 2.1 Si ya tenías datos cargados con una versión anterior

Si ya usaste esta app antes y tienes un archivo `data/inspecciones.db` con
información cargada, ejecuta los scripts de migración **una sola vez**, en
orden, antes de iniciar la app, para no perder esos datos:

```bash
# Solo si vienes de la primerísima versión (con catálogos en tablas separadas)
python database/migrate_v2.py

# Si vienes de la versión con Autor / mal_generada / observaciones / Analista_responsable
python database/migrate_v3.py
```

Cada script respalda tu base actual (`inspecciones_backup_v1.db`,
`inspecciones_backup_v2.db`) antes de tocar nada. Si tu base ya está en el
formato más reciente, el script lo detecta y no hace cambios.

## 3. Logo corporativo

Coloca tu logo en `assets/logo.png` (créala si no existe). Si el archivo
no está presente, la app funciona igual, simplemente sin logo — no genera
ningún error.

## 3.1 Descarga de tablas y gráficos en PDF

El Dashboard permite descargar tablas en Excel/PDF y gráficos en JPG/PDF.
La descarga en Excel y el JPG (ícono de cámara 📷 en cada gráfico)
funcionan siempre, sin nada adicional. Para las descargas en **PDF**
necesitas dos paquetes ya incluidos en `requirements.txt`:

- `reportlab` — genera el PDF de las tablas.
- `kaleido` — genera el PDF de los gráficos (renderiza Plotly del lado
  del servidor).

Si por algún motivo no se instalan, la app no se rompe: el botón de PDF
correspondiente simplemente muestra un aviso explicando qué instalar.

## 4. Ejecutar la aplicación

```bash
streamlit run app.py
```

Esto abrirá automáticamente el navegador en `http://localhost:8501`.
La primera vez que se ejecuta, el sistema crea la base de datos (`data/inspecciones.db`)
con catálogos base y un usuario administrador:

- **Usuario:** `admin`
- **Contraseña:** `admin123`

> ⚠️ **Importante:** ingresa al módulo de **Administración** y cambia esta
> contraseña inmediatamente, y crea ahí hasta 10 usuarios reales del equipo.

## 5. Flujo de uso diario

1. Cada persona inicia sesión con su usuario individual.
2. Va a **Formulario** y registra cada inspección del día (el campo "Autor"
   se autocompleta solo, no se puede editar).
3. En **Dashboard**, cualquier usuario puede ver en tiempo real:
   - Total de inspecciones enviadas a archivo.
   - Cuentas ingresadas más de una vez (posible duplicidad).
   - Ranking de rendimiento por Autor e Inspector.
   - Conteo de inspecciones mal generadas.
   - Reporte mensual acumulado y exportación a CSV.
4. El administrador gestiona usuarios y catálogos (áreas, sectores, inspectores)
   desde **Administración**, para mantener la captura estandarizada.

## 6. Despliegue en un servidor interno (opcional)

Si quieres que tu equipo (hasta 10 usuarios) acceda desde sus propios equipos sin instalar nada:

```bash
streamlit run app.py --server.port 8501 --server.address 0.0.0.0
```

Luego cada usuario accede desde su navegador a `http://IP_DEL_SERVIDOR:8501`.
Asegúrate de que el firewall interno permita ese puerto solo dentro de la red local.

Para dejarlo corriendo de forma permanente en un servidor Linux, puedes usar `systemd`
o `pm2`/`nohup`. Si el proyecto crece más allá de 10 usuarios o requiere acceso
concurrente más pesado, el siguiente paso natural es migrar `database/db.py` de
SQLite a PostgreSQL (la capa de queries en `utils/queries.py` ya está aislada
para facilitar ese cambio).

## 7. Respaldo de datos

Toda la información vive en un único archivo: `data/inspecciones.db`.
Para respaldar, basta con copiar ese archivo (por ejemplo, a un backup diario
automatizado con una tarea programada / cron).

## 8. Notas de diseño

- El catálogo **Detalle** tiene columnas booleanas `es_archivo` y
  `es_mal_generada` en vez de depender de coincidencias de texto libre —
  así los KPIs son exactos y no se rompen por errores de tipeo o sinónimos.
- El **número de orden** tiene una restricción de unicidad en la base de
  datos: no se puede guardar dos veces la misma orden por error.
- El sistema alerta (no bloquea) cuando una cuenta ya fue ingresada antes,
  para que el usuario verifique si es una reincidencia legítima o un duplicado.
