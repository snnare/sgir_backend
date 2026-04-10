from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Numeric, Text, BigInteger
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.db.postgres.connection import Base

# --- Catálogos de Monitoreo ---

class TipoMetrica(Base):
    __tablename__ = "tipo_metrica"
    id_tipo_metrica = Column(Integer, primary_key=True, index=True)
    nombre_tipo = Column(String(50), nullable=False)
    unidad_medida = Column(String(20), nullable=False)

class NivelAlerta(Base):
    __tablename__ = "nivel_alerta"
    id_nivel_alerta = Column(Integer, primary_key=True, index=True)
    nombre_nivel = Column(String(50), unique=True, nullable=False)

# --- Tablas de Persistencia ---

class Monitoreo(Base):
    __tablename__ = "monitoreo"
    id_monitoreo = Column(BigInteger, primary_key=True, index=True)
    fecha_inicio = Column(DateTime(timezone=True), server_default=func.now())
    fecha_fin = Column(DateTime(timezone=True), nullable=True)
    
    id_servidor = Column(Integer, ForeignKey("servidor.id_servidor", ondelete="CASCADE"), nullable=False)
    id_credencial = Column(Integer, ForeignKey("credencial_acceso.id_credencial"), nullable=False)
    id_estado_monitoreo = Column(Integer, ForeignKey("estado_general.id_estado"), nullable=False)

    # Relaciones
    metricas = relationship("Metrica", back_populates="monitoreo", cascade="all, delete-orphan")
    alertas = relationship("Alerta", back_populates="monitoreo")

class Metrica(Base):
    __tablename__ = "metrica"
    id_metrica = Column(BigInteger, primary_key=True, index=True)
    valor = Column(Numeric(10, 2), nullable=False)
    fecha_registro = Column(DateTime(timezone=True), server_default=func.now())
    
    id_monitoreo = Column(BigInteger, ForeignKey("monitoreo.id_monitoreo", ondelete="CASCADE"), nullable=False)
    id_tipo_metrica = Column(Integer, ForeignKey("tipo_metrica.id_tipo_metrica"), nullable=False)

    monitoreo = relationship("Monitoreo", back_populates="metricas")

class Alerta(Base):
    __tablename__ = "alerta"
    id_alerta = Column(BigInteger, primary_key=True, index=True)
    descripcion = Column(Text, nullable=False)
    fecha_alerta = Column(DateTime(timezone=True), server_default=func.now())
    
    id_servidor = Column(Integer, ForeignKey("servidor.id_servidor", ondelete="CASCADE"), nullable=False)
    id_monitoreo = Column(BigInteger, ForeignKey("monitoreo.id_monitoreo"), nullable=True)
    id_nivel_alerta = Column(Integer, ForeignKey("nivel_alerta.id_nivel_alerta"), nullable=False)
    id_estado_alerta = Column(Integer, ForeignKey("estado_general.id_estado"), nullable=False)

    monitoreo = relationship("Monitoreo", back_populates="alertas")
