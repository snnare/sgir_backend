from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Numeric, Text, BigInteger
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.db.postgres.postgres_connection import Base

# --- Catálogos de Backup ---

class TipoRespaldo(Base):
    __tablename__ = "tipo_respaldo"
    id_tipo_respaldo = Column(Integer, primary_key=True, index=True)
    nombre_tipo = Column(String(50), unique=True, nullable=False)

class TipoAlmacenamiento(Base):
    __tablename__ = "tipo_almacenamiento"
    id_tipo_almacenamiento = Column(Integer, primary_key=True, index=True)
    nombre_tipo = Column(String(50), unique=True, nullable=False)

# --- Tablas de Configuración ---

class RutaRespaldo(Base):
    __tablename__ = "ruta_respaldo"
    id_ruta = Column(Integer, primary_key=True, index=True)
    descripcion_ruta = Column(String(150), nullable=False)
    path = Column(Text, nullable=False)
    
    id_tipo_almacenamiento = Column(Integer, ForeignKey("tipo_almacenamiento.id_tipo_almacenamiento"), nullable=False)
    id_estado_ruta = Column(Integer, ForeignKey("estado_general.id_estado"), nullable=False)

class PoliticaRespaldo(Base):
    __tablename__ = "politica_de_respaldo"
    id_politica = Column(Integer, primary_key=True, index=True)
    nombre_politica = Column(String(100), nullable=False)
    descripcion = Column(Text)
    frecuencia_horas = Column(Integer, nullable=False)
    retencion_dias = Column(Integer, nullable=False)
    
    id_tipo_respaldo = Column(Integer, ForeignKey("tipo_respaldo.id_tipo_respaldo"), nullable=False)
    id_estado_politica = Column(Integer, ForeignKey("estado_general.id_estado"), nullable=False)

# --- Tabla Intermedia (N:M) ---

class AsignacionPoliticaBD(Base):
    __tablename__ = "asignacion_politica_bd"
    id_base_datos = Column(Integer, ForeignKey("base_de_datos.id_base_datos", ondelete="CASCADE"), primary_key=True)
    id_politica = Column(Integer, ForeignKey("política_de_respaldo.id_politica", ondelete="CASCADE"), primary_key=True)

# --- Tabla Transaccional ---

class Respaldo(Base):
    __tablename__ = "respaldo"
    id_respaldo = Column(BigInteger, primary_key=True, index=True)
    fecha_inicio = Column(DateTime(timezone=True), server_default=func.now())
    fecha_fin = Column(DateTime(timezone=True), nullable=True)
    tamano_mb = Column(Numeric(12, 2))
    hash_integridad = Column(String(255))
    
    id_base_datos = Column(Integer, ForeignKey("base_de_datos.id_base_datos"), nullable=False)
    id_politica = Column(Integer, ForeignKey("política_de_respaldo.id_politica"), nullable=False)
    id_credencial = Column(Integer, ForeignKey("credencial_acceso.id_credencial"), nullable=False)
    id_ruta_respaldo = Column(Integer, ForeignKey("ruta_respaldo.id_ruta"), nullable=False)
    id_estado_ejecucion = Column(Integer, ForeignKey("estado_general.id_estado"), nullable=False)
