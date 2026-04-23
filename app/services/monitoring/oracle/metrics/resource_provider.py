from sqlalchemy.orm import Session
from sqlalchemy import text
from decimal import Decimal

def get_group_b_resources(remote_db: Session) -> dict:
    """
    Grupo B: Hilos (procesos), Memoria y Locks.
    """
    # 1. Hilos (Procesos en el SO para Oracle)
    threads = remote_db.execute(text("SELECT count(*) FROM v$process")).scalar()
    
    # 2. Uso de Memoria SGA (MB)
    mem_usage = remote_db.execute(text("SELECT sum(value)/1024/1024 FROM v$sga")).scalar()
    
    # 3. Memoria Máxima (memory_target)
    mem_max = remote_db.execute(text("SELECT value/1024/1024 FROM v$parameter WHERE name = 'memory_target'")).scalar()
    if not mem_max or mem_max == '0':
        mem_max = mem_usage # Fallback si no está configurado target dinámico

    # 4. Locks activos que están bloqueando a otros
    locks = remote_db.execute(text("SELECT count(*) FROM v$lock WHERE block > 0")).scalar()
    
    return {
        "threads_count": threads,
        "memory_usage_mb": round(Decimal(mem_usage or 0), 2),
        "memory_max_mb": round(Decimal(mem_max or 0), 2),
        "active_locks": locks
    }
