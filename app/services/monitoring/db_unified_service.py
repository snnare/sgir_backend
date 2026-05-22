from sqlalchemy.orm import Session
from sqlalchemy import text
from app.models.monitoring_persistence_models import Monitoreo, Metrica, TipoMetrica, Alerta
from app.models.infrastructure_models import InstanciaDBMS, Servidor, CredencialAcceso, DBMS
from app.core.dynamic_db_core import get_dynamic_session
from datetime import datetime, timedelta, timezone
import logging

logger = logging.getLogger("db_unified_service")

# Caché en memoria para el Frontend (DB Cards)
LIVE_DB_CACHE = {}

def get_db_metrics_by_engine(engine_name: str, session, criticality_id: int):
    """Extrae métricas normalizadas según el motor y nivel de criticidad."""
    metrics = {"ping": 0, "capacity_pct": 0, "stuck_processes": 0, "specific_value": 0}
    
    try:
        # --- NIVEL BAJO (1) o superior: PING ---
        if engine_name == "Oracle Database":
            session.execute(text("SELECT 1 FROM DUAL"))
        else:
            session.execute(text("SELECT 1"))
        metrics["ping"] = 1

        # --- NIVEL MEDIO (2) o superior: CAPACIDAD ---
        if criticality_id >= 2:
            if engine_name == "MySQL":
                res = session.execute(text("SHOW VARIABLES LIKE 'max_connections'")).fetchone()
                max_conn = int(res[1]) if res else 100
                res = session.execute(text("SHOW STATUS LIKE 'Threads_connected'")).fetchone()
                curr_conn = int(res[1]) if res else 0
                metrics["capacity_pct"] = round((curr_conn / max_conn) * 100, 2)
            
            elif engine_name == "Oracle Database":
                res = session.execute(text("SELECT count(*) FROM v$session")).scalar()
                max_res = session.execute(text("SELECT value FROM v$parameter WHERE name = 'processes'")).scalar()
                metrics["capacity_pct"] = round((int(res) / int(max_res)) * 100, 2)

            elif engine_name == "MongoDB":
                # asumiendo que session es un MongoClient en este caso
                status = session.admin.command("serverStatus")
                curr = status["connections"]["current"]
                available = status["connections"]["available"]
                metrics["capacity_pct"] = round((curr / (curr + available)) * 100, 2)

        # --- NIVEL ALTO (3) o superior: PROCESOS ATORADOS ---
        if criticality_id >= 3:
            if engine_name == "MySQL":
                res = session.execute(text("SELECT COUNT(*) FROM information_schema.processlist WHERE Command != 'Sleep' AND Time > 30")).scalar()
                metrics["stuck_processes"] = int(res or 0)
            elif engine_name == "Oracle Database":
                res = session.execute(text("SELECT COUNT(*) FROM v$session WHERE status = 'KILLED'")).scalar()
                metrics["stuck_processes"] = int(res or 0)

        # --- NIVEL CRÍTICO (4): MÉTRICA ESPECÍFICA ---
        if criticality_id >= 4:
            if engine_name == "Oracle Database": # Uso de Tablespace Crítico
                res = session.execute(text("SELECT MAX(used_percent) FROM (SELECT ROUND((used_space/tablespace_size)*100,2) used_percent FROM dba_tablespace_usage_metrics)")).scalar()
                metrics["specific_value"] = float(res or 0)
            elif engine_name == "MySQL": # Hit Rate de Buffer Pool
                res = session.execute(text("SHOW STATUS LIKE 'Innodb_buffer_pool_read_requests'")).fetchone()
                metrics["specific_value"] = float(res[1]) if res else 0

    except Exception as e:
        logger.error(f"Error extrayendo métricas de {engine_name}: {str(e)}")
        metrics["ping"] = 0
    
    return metrics

def run_unified_db_monitoring(db: Session, instancia_id: int, credencial_id: int):
    """Servicio unificado que orquesta la conexión, extracción y persistencia."""
    instancia = db.query(InstanciaDBMS).filter(InstanciaDBMS.id_instancia == instancia_id).first()
    servidor = instancia.servidor
    credencial = db.query(CredencialAcceso).filter(CredencialAcceso.id_credencial == credencial_id).first()
    dbms = db.query(DBMS).filter(DBMS.id_dbms == instancia.id_dbms).first()

    # Iniciar Monitoreo
    nuevo_monitoreo = Monitoreo(id_servidor=servidor.id_servidor, id_estado_monitoreo=1)
    db.add(nuevo_monitoreo)
    db.commit()
    db.refresh(nuevo_monitoreo)

    remote_session = None
    try:
        # CORRECCIÓN: Para MySQL monitoreo, conectamos a information_schema para evitar error 1049.
        db_conn_name = "information_schema" if instancia.id_dbms in [2, 3] else instancia.nombre_instancia
        
        remote_session = get_dynamic_session(servidor, credencial, instancia.id_dbms, db_name=db_conn_name)
        raw_metrics = get_db_metrics_by_engine(dbms.nombre_dbms, remote_session, servidor.id_nivel_criticidad)

        # 1. Actualizar Live Cache
        LIVE_DB_CACHE[instancia_id] = {
            "engine": dbms.nombre_dbms,
            "metrics": raw_metrics,
            "last_update": datetime.now(timezone.utc)
        }

        # 2. Persistencia por Umbral (Capacidad > 90%)
        if raw_metrics["capacity_pct"] >= 90:
            tipo = db.query(TipoMetrica).filter(TipoMetrica.nombre_tipo == "DB_Capacity").first()
            if not tipo:
                tipo = TipoMetrica(nombre_tipo="DB_Capacity", unidad_medida="%")
                db.add(tipo); db.commit(); db.refresh(tipo)
            
            db.add(Metrica(valor=raw_metrics["capacity_pct"], id_monitoreo=nuevo_monitoreo.id_monitoreo, id_tipo_metrica=tipo.id_tipo_metrica))
            
            # Generar Alerta
            db.add(Alerta(
                descripcion=f"Capacidad de conexiones crítica en {instancia.nombre_instancia}: {raw_metrics['capacity_pct']}%",
                id_servidor=servidor.id_servidor, id_monitoreo=nuevo_monitoreo.id_monitoreo,
                id_nivel_alerta=3, id_estado_alerta=6
            ))

        # 3. Alerta por Caída de Ping
        if raw_metrics["ping"] == 0:
            db.add(Alerta(
                descripcion=f"Instancia {instancia.nombre_instancia} NO RESPONDE (Ping fallido)",
                id_servidor=servidor.id_servidor, id_monitoreo=nuevo_monitoreo.id_monitoreo,
                id_nivel_alerta=4, id_estado_alerta=6
            ))

        nuevo_monitoreo.id_estado_monitoreo = 4 if raw_metrics["ping"] == 1 else 5
        nuevo_monitoreo.fecha_fin = datetime.now()
        db.commit()

        return {"status": "success", "data": raw_metrics}

    except Exception as e:
        nuevo_monitoreo.id_estado_monitoreo = 5
        db.commit()
        raise e
    finally:
        if remote_session and hasattr(remote_session, 'close'):
            # Si es MongoDB (id_dbms = 5), NO cerramos el cliente para no destruir el pool global persistente.
            if instancia.id_dbms != 5:
                remote_session.close()

def get_db_health_status(db: Session, instancia_id: int):
    """Consulta para el Frontend de la salud de la DB."""
    live_data = LIVE_DB_CACHE.get(instancia_id)
    last_session = db.query(Monitoreo).join(InstanciaDBMS, InstanciaDBMS.id_servidor == Monitoreo.id_servidor).filter(
        InstanciaDBMS.id_instancia == instancia_id, Monitoreo.id_estado_monitoreo == 4
    ).order_by(Monitoreo.id_monitoreo.desc()).first()

    if not last_session: return {"status": "unknown", "message": "Sin datos"}
    
    # Determinación de color/status y métricas
    status = "healthy"
    engine_name = "N/A"
    metrics = {}
    
    if live_data:
        if isinstance(live_data, str):
            # Formato piped: status|uptime|threads_conn|max_conn|conn_usage|...
            parts = live_data.split('|')
            status_val = parts[0]
            conn_usage = float(parts[4]) if parts[4] != "N/A" else 0.0
            
            ping_val = 1 if status_val == "online" else 0
            metrics = {
                "ping": ping_val,
                "capacity_pct": conn_usage,
                "stuck_processes": int(parts[5]) if parts[5].isdigit() else 0,
                "specific_value": float(parts[13]) if parts[13] != "N/A" else 0.0
            }
            if ping_val == 0:
                status = "fatal"
            elif conn_usage >= 90:
                status = "critical"
                
            # Resolver engine desde la instancia en DB
            inst = db.query(InstanciaDBMS).filter(InstanciaDBMS.id_instancia == instancia_id).first()
            if inst and inst.dbms:
                engine_name = inst.dbms.nombre_dbms
        elif isinstance(live_data, dict):
            metrics = live_data.get("metrics", {})
            engine_name = live_data.get("engine", "N/A")
            if metrics.get("ping", 1) == 0:
                status = "fatal"
            elif metrics.get("capacity_pct", 0.0) >= 90:
                status = "critical"

    return {
        "status": status,
        "engine": engine_name,
        "metrics": metrics,
        "last_check": last_session.fecha_inicio
    }

