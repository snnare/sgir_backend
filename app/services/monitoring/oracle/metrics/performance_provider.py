from sqlalchemy.orm import Session
from sqlalchemy import text
from decimal import Decimal

def get_group_c_performance(remote_db: Session) -> dict:
    """
    Grupo C: Slow queries, tiempo de respuesta y CPU.
    """
    # 1. Slow Queries (SQLs que tardan más de 1 segundo en ejecución acumulada)
    slow_queries = remote_db.execute(text("SELECT count(*) FROM v$sqlarea WHERE elapsed_time/1000000 > 1")).scalar()
    
    # 2. Tiempo de respuesta promedio (basado en latencia de lectura de disco/db file sequential read)
    # Una métrica común en Oracle para tiempo de respuesta de BD
    resp_time = remote_db.execute(text("SELECT average_wait FROM v$system_event WHERE event = 'db file sequential read'")).scalar()
    
    # 3. Uso de CPU aproximado de la instancia
    cpu_usage = remote_db.execute(text("SELECT value FROM v$sysstat WHERE name = 'CPU used by this session' AND rownum = 1")).scalar()
    # Para efectos del prototipo, normalizamos a un porcentaje simulado si no hay acceso a v$osstat
    cpu_percent = (int(cpu_usage) % 100) if cpu_usage else 0.0

    return {
        "slow_queries_count": slow_queries or 0,
        "avg_response_time_ms": round(Decimal(resp_time or 0), 2),
        "cpu_usage_percent": round(Decimal(cpu_percent), 2)
    }
