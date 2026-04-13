-- SGIR Initialization Script

-- 1. Schema
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
    direccion_ip VARCHAR(45) NOT NULL,
    es_legacy BOOLEAN DEFAULT FALSE,
    fecha_registro TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    descripcion TEXT,
    id_nivel_criticidad INT NOT NULL REFERENCES Nivel_Criticidad(id_nivel_criticidad),
    id_estado_servidor INT NOT NULL REFERENCES Estado_General(id_estado)
);

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
    id_tipo_almacenamiento INT NOT NULL REFERENCES Tipo_Almacenamiento(id_tipo_almacenamiento),
    id_estado_ruta INT NOT NULL REFERENCES Estado_General(id_estado)
);

CREATE TABLE Política_de_Respaldo (
    id_politica INT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    nombre_politica VARCHAR(100) NOT NULL,
    descripcion TEXT,
    frecuencia_horas INT NOT NULL,
    retencion_dias INT NOT NULL,
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
    id_estado_instancia INT NOT NULL REFERENCES Estado_General(id_estado)
);

CREATE TABLE Base_de_Datos (
    id_base_datos INT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    nombre_base VARCHAR(150) NOT NULL,
    tamano_mb NUMERIC(12, 2),
    fecha_creacion TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    id_instancia INT NOT NULL REFERENCES Instancia_DBMS(id_instancia) ON DELETE CASCADE,
    id_estado_bd INT NOT NULL REFERENCES Estado_General(id_estado)
);

CREATE TABLE Monitoreo (
    id_monitoreo BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    fecha_inicio TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    fecha_fin TIMESTAMPTZ,
    id_servidor INT NOT NULL REFERENCES Servidor(id_servidor) ON DELETE CASCADE,
    id_credencial INT NOT NULL REFERENCES Credencial_Acceso(id_credencial),
    id_estado_monitoreo INT NOT NULL REFERENCES Estado_General(id_estado)
);

CREATE TABLE Asignacion_Politica_BD (
    id_base_datos INT NOT NULL REFERENCES Base_de_Datos(id_base_datos) ON DELETE CASCADE,
    id_politica INT NOT NULL REFERENCES Política_de_Respaldo(id_politica) ON DELETE CASCADE,
    PRIMARY KEY (id_base_datos, id_politica)
);

CREATE TABLE Respaldo (
    id_respaldo BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    fecha_inicio TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    fecha_fin TIMESTAMPTZ,
    tamano_mb NUMERIC(12, 2),
    hash_integridad VARCHAR(255),
    id_base_datos INT NOT NULL REFERENCES Base_de_Datos(id_base_datos),
    id_politica INT NOT NULL REFERENCES Política_de_Respaldo(id_politica),
    id_credencial INT NOT NULL REFERENCES Credencial_Acceso(id_credencial),
    id_ruta_respaldo INT NOT NULL REFERENCES Ruta_Respaldo(id_ruta),
    id_estado_ejecucion INT NOT NULL REFERENCES Estado_General(id_estado)
);

CREATE TABLE Métrica (
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
    id_monitoreo BIGINT REFERENCES Monitoreo(id_monitoreo),
    id_nivel_alerta INT NOT NULL REFERENCES Nivel_Alerta(id_nivel_alerta),
    id_estado_alerta INT NOT NULL REFERENCES Estado_General(id_estado)
);

CREATE TABLE Bitacora (
    id_bitacora BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    entidad_afectada VARCHAR(100) NOT NULL,
    id_entidad BIGINT NOT NULL,
    descripcion_evento TEXT NOT NULL,
    fecha_evento TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    id_usuario INT NOT NULL REFERENCES Usuario(id_usuario),
    id_tipo_evento INT NOT NULL REFERENCES Tipo_Evento_Auditoria(id_tipo_evento)
);

-- 2. Initial Data (Catalogs)
INSERT INTO Estado_General (nombre_estado) VALUES 
('Activo'), ('Inactivo'), ('Pendiente'), ('Fallido'), ('Completado');

INSERT INTO Rol_Usuario (nombre_rol) VALUES 
('Admin'), ('Operador');

INSERT INTO Nivel_Criticidad (nombre_nivel) VALUES 
('Bajo'), ('Medio'), ('Alto'), ('Crítico');

INSERT INTO Tipo_Acceso (nombre_tipo) VALUES 
('SSH'), ('DB Native'), ('SFTP'), ('API');

INSERT INTO Tipo_Evento_Auditoria (nombre_evento) VALUES 
('Inicio de sesión'), ('Creación'), ('Modificación'), ('Elimination'), ('Ejecución');

INSERT INTO Nivel_Alerta (nombre_nivel) VALUES 
('Informativa'), ('Advertencia'), ('Crítica');

INSERT INTO Tipo_Respaldo (nombre_tipo) VALUES 
('Full'), ('Incremental'), ('Diferencial');

INSERT INTO Tipo_Almacenamiento (nombre_tipo) VALUES 
('Local'), ('S3'), ('NAS'), ('SAN');
