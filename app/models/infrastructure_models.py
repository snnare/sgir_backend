from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Boolean, Numeric, Text
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.db.postgres.postgres_connection import Base

# --- Catálogos de Infraestructura ---

class NivelCriticidad(Base):
    __tablename__ = "nivel_criticidad"
    id_nivel_criticidad = Column(Integer, primary_key=True, index=True)
    nombre_nivel = Column(String(50), unique=True, nullable=False)
    descripcion = Column(Text)

class TipoAcceso(Base):
    __tablename__ = "tipo_acceso"
    id_tipo_acceso = Column(Integer, primary_key=True, index=True)
    nombre_tipo = Column(String(50), unique=True, nullable=False)

class DBMS(Base):
    __tablename__ = "dbms"
    id_dbms = Column(Integer, primary_key=True, index=True)
    nombre_dbms = Column(String(100), nullable=False)
    version = Column(String(50), nullable=False)
    descripcion = Column(Text)

# --- Tablas Principales ---

class Servidor(Base):
    __tablename__ = "servidor"
    id_servidor = Column(Integer, primary_key=True, index=True)
    nombre_servidor = Column(String(100), nullable=False)
    direccion_ip = Column(String(45), nullable=False)
    es_legacy = Column(Boolean, default=False)
    fecha_registro = Column(DateTime(timezone=True), server_default=func.now())
    descripcion = Column(Text)
    
    id_nivel_criticidad = Column(Integer, ForeignKey("nivel_criticidad.id_nivel_criticidad"), nullable=False)
    id_estado_servidor = Column(Integer, ForeignKey("estado_general.id_estado"), nullable=False)

    # Relaciones
    instancias = relationship("InstanciaDBMS", back_populates="servidor", cascade="all, delete-orphan")
    credenciales = relationship("CredencialAcceso", back_populates="servidor", cascade="all, delete-orphan")

class CredencialAcceso(Base):
    __tablename__ = "credencial_acceso"
    id_credencial = Column(Integer, primary_key=True, index=True)
    usuario = Column(String(100), nullable=False)
    password_hash = Column(String(255), nullable=False)
    fecha_creacion = Column(DateTime(timezone=True), server_default=func.now())
    
    id_tipo_acceso = Column(Integer, ForeignKey("tipo_acceso.id_tipo_acceso"), nullable=False)
    id_estado_credencial = Column(Integer, ForeignKey("estado_general.id_estado"), nullable=False)
    id_servidor = Column(Integer, ForeignKey("servidor.id_servidor", ondelete="CASCADE"), nullable=False)

    servidor = relationship("Servidor", back_populates="credenciales")

class InstanciaDBMS(Base):
    __tablename__ = "instancia_dbms"
    id_instancia = Column(Integer, primary_key=True, index=True)
    nombre_instancia = Column(String(100), nullable=False)
    puerto = Column(Integer, nullable=False)
    fecha_inicio = Column(DateTime(timezone=True), server_default=func.now())
    
    id_servidor = Column(Integer, ForeignKey("servidor.id_servidor", ondelete="CASCADE"), nullable=False)
    id_dbms = Column(Integer, ForeignKey("dbms.id_dbms"), nullable=False)
    id_estado_instancia = Column(Integer, ForeignKey("estado_general.id_estado"), nullable=False)

    servidor = relationship("Servidor", back_populates="instancias")
    bases_datos = relationship("BaseDeDatos", back_populates="instancia", cascade="all, delete-orphan")

class BaseDeDatos(Base):
    __tablename__ = "base_de_datos"
    id_base_datos = Column(Integer, primary_key=True, index=True)
    nombre_base = Column(String(150), nullable=False)
    tamano_mb = Column(Numeric(12, 2))
    fecha_creacion = Column(DateTime(timezone=True), server_default=func.now())
    
    id_instancia = Column(Integer, ForeignKey("instancia_dbms.id_instancia", ondelete="CASCADE"), nullable=False)
    id_estado_bd = Column(Integer, ForeignKey("estado_general.id_estado"), nullable=False)

    instancia = relationship("InstanciaDBMS", back_populates="bases_datos")

