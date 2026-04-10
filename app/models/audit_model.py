from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text, BigInteger
from sqlalchemy.sql import func
from app.db.postgres.connection import Base

class TipoEventoAuditoria(Base):
    __tablename__ = "tipo_evento_auditoria"
    id_tipo_evento = Column(Integer, primary_key=True, index=True)
    nombre_evento = Column(String(100), unique=True, nullable=False)

class Bitacora(Base):
    __tablename__ = "bitacora"
    id_bitacora = Column(BigInteger, primary_key=True, index=True)
    entidad_afectada = Column(String(100), nullable=False)
    id_entidad = Column(BigInteger, nullable=False) # Polimórfico (ID de cualquier tabla)
    descripcion_evento = Column(Text, nullable=False)
    fecha_evento = Column(DateTime(timezone=True), server_default=func.now())
    
    id_usuario = Column(Integer, ForeignKey("usuario.id_usuario"), nullable=False)
    id_tipo_evento = Column(Integer, ForeignKey("tipo_evento_auditoria.id_tipo_evento"), nullable=False)
