from sqlalchemy.orm import Session
from sqlalchemy import text
from app.schemas import MySQLConnectivityMetrics

def get_group_a_connectivity(db: Session) -> MySQLConnectivityMetrics:
    """
    Grupo A: Conectividad y Salud Básica de MySQL 5.
    Realiza consultas directas a information_schema.
    """
    try:
        # Validar socket de conexión
        db.execute(text("SELECT 1"))
        status = "online"
    except Exception:
        return MySQLConnectivityMetrics(
            status="offline",
            uptime=0,
            threads_connected=0,
            max_connections=0,
            connection_usage_percent=0.0
        )

    try:
        # Consultar global status
        try:
            status_res = db.execute(text("""
                SELECT VARIABLE_NAME, VARIABLE_VALUE 
                FROM information_schema.global_status 
                WHERE LOWER(VARIABLE_NAME) IN ('uptime', 'threads_connected')
            """)).fetchall()
        except Exception:
            status_res = db.execute(text("""
                SELECT VARIABLE_NAME, VARIABLE_VALUE 
                FROM performance_schema.global_status 
                WHERE LOWER(VARIABLE_NAME) IN ('uptime', 'threads_connected')
            """)).fetchall()
        stats = {row[0].lower(): row[1] for row in status_res}

        # Consultar global variables
        try:
            var_res = db.execute(text("""
                SELECT VARIABLE_VALUE 
                FROM information_schema.global_variables 
                WHERE LOWER(VARIABLE_NAME) = 'max_connections'
            """)).fetchone()
        except Exception:
            var_res = db.execute(text("""
                SELECT VARIABLE_VALUE 
                FROM performance_schema.global_variables 
                WHERE LOWER(VARIABLE_NAME) = 'max_connections'
            """)).fetchone()
        max_conn = int(var_res[0]) if var_res and var_res[0] else 151

        uptime = int(stats.get('uptime', 0))
        threads_connected = int(stats.get('threads_connected', 0))
        conn_usage = round((threads_connected / max_conn) * 100, 2) if max_conn > 0 else 0.0

        return MySQLConnectivityMetrics(
            status=status,
            uptime=uptime,
            threads_connected=threads_connected,
            max_connections=max_conn,
            connection_usage_percent=conn_usage
        )
    except Exception as e:
        # Fallback si information_schema no está totalmente accesible o configurado
        return MySQLConnectivityMetrics(
            status="error",
            uptime=0,
            threads_connected=0,
            max_connections=0,
            connection_usage_percent=0.0
        )
