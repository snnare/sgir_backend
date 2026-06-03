-- ==============================================================================
-- SISTEMA DE GESTIÓN DE INFRAESTRUCTURA Y RESPALDOS (SGIR)
-- MODELO FÍSICO PARA POSTGRESQL 16
-- ==============================================================================

-- ------------------------------------------------------------------------------
-- 1. CREACIÓN DE CATÁLOGOS (Tablas sin llaves foráneas)
-- ------------------------------------------------------------------------------

CREATE TABLE Estado_General (
    id_estado INT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    nombre_estado VARCHAR(50) NOT NULL UNIQUE
);

CREATE TABLE Rol_Usuario (
    id_rol INT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    nombre_rol VARCHAR(50) NOT NULL UNIQUE
);

CREATE TABLE Nivel_Criticidad (
    id_nivel_criticidad INT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    nombre_nivel VARCHAR(50) NOT NULL UNIQUE,
    descripcion TEXT
);

CREATE TABLE Tipo_Acceso (
    id_tipo_acceso INT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    nombre_tipo VARCHAR(50) NOT NULL UNIQUE
);

CREATE TABLE DBMS (
    id_dbms INT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    nombre_dbms VARCHAR(100) NOT NULL,
    version VARCHAR(50) NOT NULL,
    descripcion TEXT
);

CREATE TABLE Tipo_Respaldo (
    id_tipo_respaldo INT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    nombre_tipo VARCHAR(50) NOT NULL UNIQUE
);

CREATE TABLE Tipo_Almacenamiento (
    id_tipo_almacenamiento INT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    nombre_tipo VARCHAR(50) NOT NULL UNIQUE
);

CREATE TABLE Nivel_Alerta (
    id_nivel_alerta INT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    nombre_nivel VARCHAR(50) NOT NULL UNIQUE
);

CREATE TABLE Tipo_Metrica (
    id_tipo_metrica INT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    nombre_tipo VARCHAR(50) NOT NULL,
    unidad_medida VARCHAR(20) NOT NULL
);

CREATE TABLE Tipo_Evento_Auditoria (
    id_tipo_evento INT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    nombre_evento VARCHAR(100) NOT NULL UNIQUE
);

-- ------------------------------------------------------------------------------
-- 2. TABLAS PRINCIPALES (NIVEL 1)
-- ------------------------------------------------------------------------------

CREATE TABLE Usuario (
    id_usuario INT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    nombres VARCHAR(100) NOT NULL,
    apellidos VARCHAR(100) NOT NULL,
    email VARCHAR(150) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    fecha_creacion TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    id_rol INT NOT NULL REFERENCES Rol_Usuario(id_rol),
    id_estado_usuario INT NOT NULL REFERENCES Estado_General(id_estado)
);

CREATE TABLE Servidor (
    id_servidor INT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    nombre_servidor VARCHAR(100) NOT NULL,
    direccion_ip VARCHAR(45) NOT NULL, -- Soporta IPv4 e IPv6
    es_legacy BOOLEAN DEFAULT FALSE,
    fecha_registro TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    descripcion TEXT,
    monitoreo_host BOOLEAN DEFAULT FALSE,
    monitoreo_db BOOLEAN DEFAULT FALSE,
    id_nivel_criticidad INT NOT NULL REFERENCES Nivel_Criticidad(id_nivel_criticidad),
    id_estado_servidor INT NOT NULL REFERENCES Estado_General(id_estado)
);
--- Se cambio de Servidor_Particion a Particion
CREATE TABLE Particion (
    id_particion INT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    id_servidor INT NOT NULL REFERENCES Servidor(id_servidor) ON DELETE CASCADE,
    path TEXT NOT NULL,
    etiqueta VARCHAR(100) NOT NULL,
    fecha_registro TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

-- ------------------------------------------------------------------------------
-- 3. TABLAS PRINCIPALES (NIVEL 2)
-- ------------------------------------------------------------------------------ 

CREATE TABLE Credencial_Acceso (
    id_credencial INT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    usuario VARCHAR(100) NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    fecha_creacion TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    id_tipo_acceso INT NOT NULL REFERENCES Tipo_Acceso(id_tipo_acceso),
    id_estado_credencial INT NOT NULL REFERENCES Estado_General(id_estado),
    id_servidor INT NOT NULL REFERENCES Servidor(id_servidor) ON DELETE CASCADE
);

CREATE TABLE Ruta_Respaldo (
    id_ruta INT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    descripcion_ruta VARCHAR(150) NOT NULL,
    path TEXT NOT NULL,
    id_servidor INT NOT NULL REFERENCES Servidor(id_servidor) ON DELETE CASCADE,
    id_tipo_almacenamiento INT NOT NULL REFERENCES Tipo_Almacenamiento(id_tipo_almacenamiento),
    id_estado_ruta INT NOT NULL REFERENCES Estado_General(id_estado)
);

--- atributo hora_ejecuccion -> hora_ejecucion
CREATE TABLE Politica_de_Respaldo (
    id_politica INT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    nombre_politica VARCHAR(100) NOT NULL,
    descripcion TEXT,
    expression_cron VARCHAR(100),
    hora_ejecucion TIME,
    dias_semana VARCHAR(50),
    frecuencia_horas INT NOT NULL,
    retencion_dias INT NOT NULL,
    script_path VARCHAR(512),
    id_tipo_respaldo INT NOT NULL REFERENCES Tipo_Respaldo(id_tipo_respaldo),
    id_estado_politica INT NOT NULL REFERENCES Estado_General(id_estado)
);

CREATE TABLE Instancia_DBMS (
    id_instancia INT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    nombre_instancia VARCHAR(100) NOT NULL,
    puerto INT NOT NULL,
    fecha_inicio TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    id_servidor INT NOT NULL REFERENCES Servidor(id_servidor) ON DELETE CASCADE,
    id_dbms INT NOT NULL REFERENCES DBMS(id_dbms),
    id_estado_instancia INT NOT NULL REFERENCES Estado_General(id_estado),
    parametros_conexion JSONB DEFAULT '{}'::jsonb
);

-- ------------------------------------------------------------------------------
-- 4. TABLAS PRINCIPALES (NIVEL 3)
-- ------------------------------------------------------------------------------

CREATE TABLE Base_de_Datos (
    id_base_datos INT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    nombre_base VARCHAR(150) NOT NULL,
    tamano_mb NUMERIC(12, 2), -- Permite almacenar tamaños precisos
    fecha_creacion TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    id_instancia INT NOT NULL REFERENCES Instancia_DBMS(id_instancia) ON DELETE CASCADE,
    id_estado_bd INT NOT NULL REFERENCES Estado_General(id_estado)
);

CREATE TABLE Monitoreo (
    id_monitoreo BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY, -- BIGINT por volumen
    fecha_inicio TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    fecha_fin TIMESTAMPTZ,
    id_servidor INT NOT NULL REFERENCES Servidor(id_servidor) ON DELETE CASCADE,
    id_estado_monitoreo INT NOT NULL REFERENCES Estado_General(id_estado)
);

-- ------------------------------------------------------------------------------
-- 5. TABLAS TRANSACCIONALES E INTERMEDIAS (Gran volumen de datos)
-- ------------------------------------------------------------------------------

CREATE TABLE Asignacion_Politica_BD (
    id_base_datos INT NOT NULL REFERENCES Base_de_Datos(id_base_datos) ON DELETE CASCADE,
    id_politica INT NOT NULL REFERENCES Politica_de_Respaldo(id_politica) ON DELETE CASCADE,
    PRIMARY KEY (id_base_datos, id_politica) -- Llave primaria compuesta
);

CREATE TABLE Respaldo (
  id_respaldo BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  fecha_inicio TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
  fecha_fin TIMESTAMPTZ,
  fecha_descubrimiento TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
  nombre_archivo VARCHAR(255),
  tamano_mb NUMERIC(12, 2),
  hash_integridad VARCHAR(255),
  path_fisico_origen VARCHAR(512),
  ubicacion_actual VARCHAR(50) DEFAULT 'Origen',
  ip_almacenado_actual VARCHAR(50),
  path_fisico_actual VARCHAR(512),
  id_base_datos INT NOT NULL REFERENCES Base_de_Datos(id_base_datos),
  id_politica INT NOT NULL REFERENCES Politica_de_Respaldo(id_politica),
  id_credencial INT REFERENCES Credencial_Acceso(id_credencial),
  id_estado_ejecucion INT NOT NULL REFERENCES Estado_General(id_estado),
  metadata_tecnica JSON DEFAULT '{}'::jsonb
);

CREATE TABLE Metrica (
    id_metrica BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    valor NUMERIC(10, 2) NOT NULL,
    fecha_registro TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    id_monitoreo BIGINT NOT NULL REFERENCES Monitoreo(id_monitoreo) ON DELETE CASCADE,
    id_tipo_metrica INT NOT NULL REFERENCES Tipo_Metrica(id_tipo_metrica)
);

CREATE TABLE Alerta (
    id_alerta BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    descripcion TEXT NOT NULL,
    fecha_alerta TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    id_servidor INT NOT NULL REFERENCES Servidor(id_servidor) ON DELETE CASCADE,
    id_monitoreo BIGINT REFERENCES Monitoreo(id_monitoreo), -- Puede ser NULL si la alerta no viene del monitoreo directo
    id_nivel_alerta INT NOT NULL REFERENCES Nivel_Alerta(id_nivel_alerta),
    id_estado_alerta INT NOT NULL REFERENCES Estado_General(id_estado)
);

CREATE TABLE Bitacora (
    id_bitacora BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    entidad_afectada VARCHAR(100) NOT NULL,
    id_entidad BIGINT NOT NULL, -- Sin FK por ser polimórfico, BIGINT para cubrir cualquier ID
    descripcion_evento TEXT NOT NULL,
    fecha_evento TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    id_usuario INT NOT NULL REFERENCES Usuario(id_usuario),
    id_tipo_evento INT NOT NULL REFERENCES Tipo_Evento_Auditoria(id_tipo_evento)
);
