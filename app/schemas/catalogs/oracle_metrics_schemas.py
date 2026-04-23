from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
from decimal import Decimal

# Grupo A: Conectividad e Inventario
class ConnectivityMetrics(BaseModel):
    status: str
    active_connections: int
    max_connections: int
    total_databases: int
    uptime_seconds: Optional[int] = None

# Grupo B: Recursos y Concurrencia
class ResourceMetrics(BaseModel):
    threads_count: int
    memory_usage_mb: Decimal
    memory_max_mb: Decimal
    active_locks: int

# Grupo C: Rendimiento
class PerformanceMetrics(BaseModel):
    slow_queries_count: int
    avg_response_time_ms: Decimal
    cpu_usage_percent: Decimal

# Respuesta Unificada
class OracleAllMetrics(BaseModel):
    instancia_id: int
    timestamp: datetime
    criticidad: str
    group_a: ConnectivityMetrics
    group_b: Optional[ResourceMetrics] = None
    group_c: Optional[PerformanceMetrics] = None
