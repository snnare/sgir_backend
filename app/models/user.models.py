from sqlalchemy import Column, Integer, String, DateTime, ForeingKey, Boolean
from sqlalchemy.sql import func
from app.db.postgres.connection import Base


class Role(Base):
    __tablename__ = "rol_usuario"
    id_rol = Column(Integer, primary_key=True, index=True)
    nombre_rol = Column(String(50), unique=True, nullable=False)


class UserStatus(Base):
    __tablename__ = "estado_general"
    id_estado = Column(Integer, primary_key=True, index=True)
    nombre_estado = Column(String(50), unique=True, nullable=False)


class User(Base):
    __tablename__ = "usuario"

    id_usuario = Column(Integer, primary_key=True, index=True)
    nombres = Column(String(100), nullable=False)
    apellidos = Column(String(100), nullable=False)
    email = Column(String(150), unique=True, index=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    fecha_creacion = Column(DateTime(timezone=True), server_default=func.now())
    id_rol = Column(Integer, ForeingKey("rol_usuario.id_rol"), nullable=False)
    id_estado_usuario = Column(Integer, ForeingKey(
        "estado_general.id_estado", nullable=False))
