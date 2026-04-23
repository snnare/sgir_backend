from sqlalchemy.orm import Session
from sqlalchemy import text

def get_group_a_connectivity(remote_db: Session) -> dict:
    """
    Grupo A: Conectividad e Inventario básico.
    """
    # 1. Conexiones Activas
    active_conn = remote_db.execute(text("SELECT count(*) FROM v$session WHERE status = 'ACTIVE'")).scalar()
    
    # 2. Conexiones Máximas (Parámetro processes)
    max_conn = remote_db.execute(text("SELECT value FROM v$parameter WHERE name = 'processes'")).scalar()
    
    # 3. Total de PDBs (Bases de datos lógicas)
    total_dbs = remote_db.execute(text("SELECT count(*) FROM v$pdbs")).scalar()
    
    return {
        "status": "UP",
        "active_connections": active_conn,
        "max_connections": int(max_conn) if max_conn else 0,
        "total_databases": total_dbs or 1
    }
