from pydantic import BaseModel, ConfigDict
from typing import Optional, List
from datetime import datetime
from decimal import Decimal

# --- Catálogos ---

class TipoMetricaBase(BaseModel):
    nombre_tipo: str
    unidad_medida: str

class TipoMetricaCreate(TipoMetricaBase):
    pass

class TipoMetricaResponse(TipoMetricaBase):
    id_tipo_metrica: int
    model_config = ConfigDict(from_attributes=True)

class NivelAlertaBase(BaseModel):
    nombre_nivel: str

class NivelAlertaCreate(NivelAlertaBase):
    pass

class NivelAlertaResponse(NivelAlertaBase):
    id_nivel_alerta: int
    model_config = ConfigDict(from_attributes=True)

# --- Métricas Históricas ---

class MetricaBase(BaseModel):
    valor: Decimal
    id_monitoreo: int
    id_tipo_metrica: int

class MetricaCreate(MetricaBase):
    pass

class MetricaResponse(MetricaBase):
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

class MonitoreoResponse(MonitoreoBase):
    id_monitoreo: int
    fecha_inicio: datetime
    fecha_fin: Optional[datetime] = None
    metricas: List[MetricaResponse] = []
    model_config = ConfigDict(from_attributes=True)

# --- Métricas Específicas por Motor ---

class MySQL5Metrics(BaseModel):
    status: str
    uptime: int
    threads_connected: int
    threads_running: int
    max_connections: int
    questions: int
    queries_per_second: float
    slow_queries: int
    table_locks_waited: int
    innodb_row_lock_waits: int
    connection_usage_percent: float

# --- Alertas ---

class AlertaBase(BaseModel):
    descripcion: str
    id_servidor: int
    id_monitoreo: Optional[int] = None
    id_nivel_alerta: int
    id_estado_alerta: int

class AlertaCreate(AlertaBase):
    pass

class AlertaResponse(AlertaBase):
    id_alerta: int
    fecha_alerta: datetime
    model_config = ConfigDict(from_attributes=True)
