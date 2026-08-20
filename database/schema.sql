-- =========================================================
-- ESQUEMA DE BASE DE DATOS v3 - Plataforma de Gestión de Inspecciones
-- Cambios respecto a v2:
--   - Se elimina autor_id (ya no se guarda quién capturó cada fila).
--   - Se elimina mal_generada.
--   - Se elimina observaciones.
--   - analista_responsable se unifica con el antiguo "autor" en un
--     único campo: analista.
-- Área destino, Detalle, Inspector, Analista y Sector siguen siendo
-- listas fijas definidas en config/constants.py (Detalle además depende
-- del Área destino elegida).
-- =========================================================

-- Usuarios del sistema (login / control de acceso a Administración y
-- Base Consolidada). Ya no se vincula a cada inspección individual.
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    nombre_completo TEXT NOT NULL,
    rol TEXT NOT NULL DEFAULT 'operador' CHECK (rol IN ('operador', 'administrador')),
    activo INTEGER NOT NULL DEFAULT 1,
    created_at TEXT DEFAULT (datetime('now'))
);

-- Tabla principal: Inspecciones
CREATE TABLE IF NOT EXISTS inspecciones (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    fecha TEXT NOT NULL,                 -- YYYY-MM-DD
    numero_cuenta TEXT NOT NULL,
    numero_orden TEXT NOT NULL,
    area_destino TEXT NOT NULL,          -- valor exacto de config.constants.AREAS_DESTINO
    detalle TEXT NOT NULL,               -- debe pertenecer a AREA_DETALLE_MAP[area_destino]
    sector TEXT NOT NULL,                -- código, ej. "1-11" (clave de SECTOR_LUGAR)
    lugar TEXT NOT NULL,                 -- se recalcula siempre a partir de "sector"
    inspector TEXT NOT NULL,             -- valor exacto de config.constants.INSPECTORES
    analista TEXT NOT NULL,              -- valor exacto de config.constants.ANALISTAS
    created_at TEXT DEFAULT (datetime('now')),
    updated_at TEXT DEFAULT (datetime('now'))
);

-- Evita el mismo número de orden duplicado por error de tipeo
CREATE UNIQUE INDEX IF NOT EXISTS idx_orden_unica ON inspecciones(numero_orden);

-- Índices para acelerar KPIs y filtros
CREATE INDEX IF NOT EXISTS idx_insp_fecha ON inspecciones(fecha);
CREATE INDEX IF NOT EXISTS idx_insp_cuenta ON inspecciones(numero_cuenta);
CREATE INDEX IF NOT EXISTS idx_insp_area ON inspecciones(area_destino);
CREATE INDEX IF NOT EXISTS idx_insp_analista ON inspecciones(analista);
CREATE INDEX IF NOT EXISTS idx_insp_inspector ON inspecciones(inspector);
