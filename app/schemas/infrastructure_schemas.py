from pydantic import BaseModel, ConfigDict
from typing import Optional, List
from datetime import datetime
from decimal import Decimal

# --- Catálogos ---

class NivelCriticidadBase(BaseModel):
    nombre_nivel: str
    descripcion: Optional[str] = None

class NivelCriticidad(NivelCriticidadBase):
    id_nivel_criticidad: int
    model_config = ConfigDict(from_attributes=True)

class TipoAcceso(BaseModel):
    id_tipo_acceso: int
    nombre_tipo: str
    model_config = ConfigDict(from_attributes=True)

class DBMS(BaseModel):
    id_dbms: int
    nombre_dbms: str
    version: str
    model_config = ConfigDict(from_attributes=True)

# --- Servidor ---

class ServidorBase(BaseModel):
    nombre_servidor: str
    direccion_ip: str
    es_legacy: bool = False
    descripcion: Optional[str] = None
    id_nivel_criticidad: int
    id_estado_servidor: int

class ServidorCreate(ServidorBase):
    pass

class Servidor(ServidorBase):
    id_servidor: int
    fecha_registro: datetime
    model_config = ConfigDict(from_attributes=True)

# --- Credencial ---

class CredencialBase(BaseModel):
    usuario: str
    id_tipo_acceso: int
    id_estado_credencial: int
    id_servidor: int

class CredencialCreate(CredencialBase):
    password: str # Se recibirá en claro para hashear

class Credencial(CredencialBase):
    id_credencial: int
    fecha_creacion: datetime
    model_config = ConfigDict(from_attributes=True)

# --- Instancia DBMS ---

class InstanciaBase(BaseModel):
    nombre_instancia: str
    puerto: int
    id_servidor: int
    id_dbms: int
    id_estado_instancia: int

class InstanciaCreate(InstanciaBase):
    pass

class Instancia(InstanciaBase):
    id_instancia: int
    fecha_inicio: datetime
    model_config = ConfigDict(from_attributes=True)

# --- Base de Datos ---

class BaseDatosBase(BaseModel):
    nombre_base: str
    tamano_mb: Optional[Decimal] = None
    id_instancia: int
    id_estado_bd: int

class BaseDatosCreate(BaseDatosBase):
    pass

class BaseDatos(BaseDatosBase):
    id_base_datos: int
    fecha_creacion: datetime
    model_config = ConfigDict(from_attributes=True)
