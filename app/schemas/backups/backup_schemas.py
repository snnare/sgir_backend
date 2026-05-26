from pydantic import BaseModel, Field
from datetime import datetime, time
from typing import Optional, List
from decimal import Decimal

# --- Catálogos ---

class TipoRespaldoBase(BaseModel):
    nombre_tipo: str

class TipoRespaldoCreate(TipoRespaldoBase):
    pass

class TipoRespaldoResponse(TipoRespaldoBase):
    id_tipo_respaldo: int
    class Config:
        from_attributes = True

class TipoAlmacenamientoBase(BaseModel):
    nombre_tipo: str

class TipoAlmacenamientoCreate(TipoAlmacenamientoBase):
    pass

class TipoAlmacenamientoResponse(TipoAlmacenamientoBase):
    id_tipo_almacenamiento: int
    class Config:
        from_attributes = True

# --- Rutas de Respaldo ---

class RutaRespaldoBase(BaseModel):
    descripcion_ruta: str
    path: str
    id_servidor: int
    id_tipo_almacenamiento: int
    id_estado_ruta: int = 1

class RutaRespaldoCreate(RutaRespaldoBase):
    pass

class RutaRespaldoUpdate(BaseModel):
    descripcion_ruta: Optional[str] = None
    path: Optional[str] = None
    id_servidor: Optional[int] = None
    id_tipo_almacenamiento: Optional[int] = None
    id_estado_ruta: Optional[int] = None

class RutaRespaldoResponse(RutaRespaldoBase):
    id_ruta: int
    class Config:
        from_attributes = True

# --- Políticas de Respaldo ---

class PoliticaRespaldoBase(BaseModel):
    nombre_politica: str
    descripcion: Optional[str] = None
    expression_cron: Optional[str] = None
    hora_ejecuccion: Optional[time] = None
    dias_semana: Optional[str] = None
    frecuencia_horas: int = Field(..., ge=1, description="Frecuencia en horas (mínimo 1)")
    retencion_dias: int = Field(..., ge=1, description="Días de retención (mínimo 1)")
    script_path: Optional[str] = None
    id_tipo_respaldo: int
    id_estado_politica: int = 1

class PoliticaRespaldoCreate(PoliticaRespaldoBase):
    pass

class PoliticaRespaldoUpdate(BaseModel):
    nombre_politica: Optional[str] = None
    descripcion: Optional[str] = None
    expression_cron: Optional[str] = None
    hora_ejecuccion: Optional[time] = None
    dias_semana: Optional[str] = None
    frecuencia_horas: Optional[int] = None
    retencion_dias: Optional[int] = None
    script_path: Optional[str] = None
    id_tipo_respaldo: Optional[int] = None
    id_estado_politica: Optional[int] = None

class PoliticaRespaldoResponse(PoliticaRespaldoBase):
    id_politica: int
    class Config:
        from_attributes = True

# --- Schemas para Vista de Detalle Enriquecida ---

class DatabaseSimpleInfo(BaseModel):
    id_base_datos: int
    nombre_base: str
    tamano_mb: Optional[Decimal] = None
    estado: str

class ServidorGroupedAssets(BaseModel):
    ip: str
    motor: str
    databases: List[DatabaseSimpleInfo]

class PoliticaDetalleAssetsResponse(BaseModel):
    id_politica: int
    nombre_politica: str
    descripcion: Optional[str] = None
    frecuencia_horas: int
    retencion_dias: int
    servidores_vinculados: List[ServidorGroupedAssets]
    
    class Config:
        from_attributes = True

# --- Asignaciones ---

class AsignacionPoliticaBDCreate(BaseModel):
    id_base_datos: int
    id_politica: int

# --- Ejecuciones de Respaldo (Auditoría) ---

class RespaldoBase(BaseModel):
    fecha_inicio: Optional[datetime] = None
    fecha_fin: Optional[datetime] = None
    fecha_descubrimiento: Optional[datetime] = None
    
    nombre_archivo: Optional[str] = None
    tamano_mb: Optional[Decimal] = None
    hash_integridad: Optional[str] = None
    
    path_fisico_origen: Optional[str] = None
    ubicacion_actual: Optional[str] = "Origen"
    ip_almacenado_actual: Optional[str] = None
    path_fisico_actual: Optional[str] = None
    
    id_base_datos: int
    id_politica: int
    id_credencial: Optional[int] = None
    id_estado_ejecucion: int # 4: Éxito, 5: Fallo
    
    metadata_tecnica: Optional[dict] = None

class RespaldoCreate(RespaldoBase):
    pass

class RespaldoResponse(RespaldoBase):
    id_respaldo: int
    class Config:
        from_attributes = True

# --- DTO para el Auditor ---

class BackupDiscoveryResult(BaseModel):
    base_datos_id: int
    nombre_base: str
    politica_nombre: str
    ruta_path: str
    archivo_encontrado: bool
    tamano_encontrado_mb: Optional[Decimal] = None
    timestamp_verificacion: datetime = Field(default_factory=datetime.now)
    detalle: Optional[str] = None
