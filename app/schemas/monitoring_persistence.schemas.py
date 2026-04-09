from pydantic import BaseModel, ConfigDict
from typing import Optional, List
from datetime import datetime
from decimal import Decimal

# --- Métricas Históricas ---

class TipoMetricaBase(BaseModel):
    nombre_tipo: str
    unidad_medida: str

class TipoMetrica(TipoMetricaBase):
    id_tipo_metrica: int
    model_config = ConfigDict(from_attributes=True)

class MetricaBase(BaseModel):
    valor: Decimal
    id_monitoreo: int
    id_tipo_metrica: int

class MetricaCreate(MetricaBase):
    pass

class Metrica(MetricaBase):
    id_metrica: int
    fecha_registro: datetime
    model_config = ConfigDict(from_attributes=True)

# --- Sesión de Monitoreo ---

class MonitoreoBase(BaseModel):
    id_servidor: int
    id_credencial: int
    id_estado_monitoreo: int

class MonitoreoCreate(MonitoreoBase):
    pass

class Monitoreo(MonitoreoBase):
    id_monitoreo: int
    fecha_inicio: datetime
    fecha_fin: Optional[datetime] = None
    metricas: List[Metrica] = []
    model_config = ConfigDict(from_attributes=True)

# --- Alertas ---

class AlertaBase(BaseModel):
    descripcion: str
    id_servidor: int
    id_monitoreo: Optional[int] = None
    id_nivel_alerta: int
    id_estado_alerta: int

class AlertaCreate(AlertaBase):
    pass

class Alerta(AlertaBase):
    id_alerta: int
    fecha_alerta: datetime
    model_config = ConfigDict(from_attributes=True)
