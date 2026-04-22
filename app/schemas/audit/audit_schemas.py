from pydantic import BaseModel
from datetime import datetime
from typing import Optional

# Schemas para Tipo de Evento de Auditoría
class TipoEventoBase(BaseModel):
    nombre_evento: str

class TipoEventoCreate(TipoEventoBase):
    pass

class TipoEventoResponse(TipoEventoBase):
    id_tipo_evento: int

    class Config:
        from_attributes = True

# Schemas para Bitácora
class BitacoraBase(BaseModel):
    entidad_afectada: str
    id_entidad: int
    descripcion_evento: str
    id_usuario: int
    id_tipo_evento: int

class BitacoraCreate(BitacoraBase):
    pass

class BitacoraResponse(BitacoraBase):
    id_bitacora: int
    fecha_evento: datetime

    class Config:
        from_attributes = True
