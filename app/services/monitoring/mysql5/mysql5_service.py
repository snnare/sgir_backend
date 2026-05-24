from sqlalchemy.orm import Session
from sqlalchemy import text
from app.schemas import MySQL5Metrics
from datetime import datetime
from app.models.infrastructure_models import InstanciaDBMS, NivelCriticidad
from app.core.dynamic_db_core import get_dynamic_session
from app.services import get_credencial
from app.services.monitoring.mysql5.metrics.connectivity_provider import get_group_a_connectivity
from app.services.monitoring.mysql5.metrics.resource_provider import get_group_b_resources
from app.services.monitoring.mysql5.metrics.performance_provider import get_group_c_performance

def get_mysql5_metrics(db: Session) -> MySQL5Metrics:
    """
    Extrae métricas de rendimiento de un servidor MySQL 5.
    """
    # 1. Verificar salud básica
    try:
        db.execute(text("SELECT 1"))
        status = "online"
    except Exception:
        status = "offline"
        return MySQL5Metrics(
            status=status, uptime=0, threads_connected=0, threads_running=0,
            max_connections=0, questions=0, queries_per_second=0.0,
            slow_queries=0, table_locks_waited=0, innodb_row_lock_waits=0,
            connection_usage_percent=0.0
        )

    # 2. Obtener Global Status
    status_result = db.execute(text("""
        SHOW GLOBAL STATUS WHERE Variable_name IN (
            'Uptime', 'Threads_connected', 'Threads_running', 
            'Questions', 'Slow_queries', 'Table_locks_waited', 
            'Innodb_row_lock_waits'
        )
    """)).fetchall()
    
    stats = {row[0]: row[1] for row in status_result}

    # 3. Obtener Variables (Límites)
    vars_result = db.execute(text("SHOW VARIABLES LIKE 'max_connections'")).fetchone()
    max_conn = int(vars_result[1]) if vars_result else 1
 
    # 4. Cálculos
    uptime = int(stats.get('Uptime', 0))
    questions = int(stats.get('Questions', 0))
    threads_connected = int(stats.get('Threads_connected', 0))
    
    qps = round(questions / uptime, 2) if uptime > 0 else 0.0
    conn_usage = round((threads_connected / max_conn) * 100, 2)

    return MySQL5Metrics(
        status=status,
        uptime=uptime,
        threads_connected=threads_connected,
        threads_running=int(stats.get('Threads_running', 0)),
        max_connections=max_conn,
        questions=questions,
        queries_per_second=qps,
        slow_queries=int(stats.get('Slow_queries', 0)),
        table_locks_waited=int(stats.get('Table_locks_waited', 0)),
        innodb_row_lock_waits=int(stats.get('Innodb_row_lock_waits', 0)),
        connection_usage_percent=conn_usage
    )

def list_databases_discovery(db: Session) -> list[dict]:
    """
    Lista todas las bases de datos reales y su tamaño en MB.
    Excluye esquemas de sistema.
    """
    query = text("""
        SELECT 
            table_schema as name,
            SUM(data_length + index_length) / 1024 / 1024 as size_mb
        FROM information_schema.tables
        WHERE table_schema NOT IN ('information_schema', 'mysql', 'performance_schema', 'sys')
        GROUP BY table_schema
    """)
    result = db.execute(query).fetchall()
    return [{"nombre": row[0], "tamano_mb": float(row[1] or 0)} for row in result]

def run_mysql5_modular_monitoring(db: Session, id_instancia: int, id_credencial: int) -> dict:
    """
    Orquesta la recolección de métricas modulares de MySQL 5 de acuerdo a la criticidad del servidor.
    """
    # 1. Obtener Instancia y Servidor
    instancia = db.query(InstanciaDBMS).filter(InstanciaDBMS.id_instancia == id_instancia).first()
    if not instancia:
        return {"error": "Instancia MySQL 5 no encontrada"}
        
    servidor = instancia.servidor
    if not servidor:
        return {"error": "Servidor no asociado a la instancia"}

    criticidad_id = servidor.id_nivel_criticidad
    criticidad_obj = db.query(NivelCriticidad).filter(NivelCriticidad.id_nivel_criticidad == criticidad_id).first()
    criticidad_nombre = criticidad_obj.nombre_nivel if criticidad_obj else "Desconocido"

    # 2. Obtener Credencial
    credencial = get_credencial(db, id_credencial)
    if not credencial:
        return {"error": "Credencial no encontrada"}

    remote_session = None
    try:
        # Conexión dinámica (para evitar error 1049, conectamos a 'information_schema')
        remote_session = get_dynamic_session(
            servidor, 
            credencial, 
            dbms_id=2, 
            db_name="information_schema", 
            parametros=instancia.parametros_conexion
        )
        
        timestamp = datetime.now()

        # Grupo A (Siempre)
        grupo_a = get_group_a_connectivity(remote_session)
        
        grupo_b = None
        if criticidad_id >= 2 and grupo_a.status == "online": # Medio, Alto, Crítico
            grupo_b = get_group_b_resources(remote_session, grupo_a.uptime)

        grupo_c = None
        if criticidad_id >= 3 and grupo_a.status == "online": # Alto, Crítico
            grupo_c = get_group_c_performance(remote_session)

        return {
            "id_instancia": id_instancia,
            "id_servidor": servidor.id_servidor,
            "nivel_criticidad": criticidad_nombre,
            "timestamp": timestamp,
            "grupo_a": grupo_a,
            "grupo_b": grupo_b,
            "grupo_c": grupo_c
        }
    except Exception as e:
        return {"error": f"Fallo en monitoreo modular MySQL 5: {str(e)}"}
    finally:
        if remote_session:
            remote_session.close()

