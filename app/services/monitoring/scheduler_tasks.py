from sqlalchemy.orm import Session
from app.db.postgres.postgres_connection import SessionLocal
from app.models.infrastructure_models import Servidor, InstanciaDBMS, CredencialAcceso, NivelCriticidad
from app.services.monitoring.ssh_service import run_ssh_monitoring
from app.services.monitoring.db_unified_service import LIVE_DB_CACHE
from app.services.monitoring.mysql5.mysql5_service import run_mysql5_modular_monitoring
from app.services.monitoring.mysql8.mysql8_service import run_mysql8_modular_monitoring
from app.services.monitoring.oracle.oracle_monitoring_service import run_oracle_modular_monitoring
from app.services.monitoring.mongodb.mongodb_service import run_mongodb_modular_monitoring
from app.models.monitoring_persistence_models import Monitoreo, Metrica, TipoMetrica, Alerta
from app.services.catalogs.monitoring_persistence_crud import purge_old_monitoring_data
from app.services.backups.retention_manager import run_backup_retention_policy
from datetime import datetime, timezone
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("scheduler_tasks")

def backup_retention_task():
    """Tarea para marcar como expirados los respaldos fuera de política."""
    db = SessionLocal()
    try:
        logger.info("Ejecutando política de retención de RESPALDOS...")
        expired_count = run_backup_retention_policy(db)
        logger.info(f"Proceso de respaldos finalizado. {expired_count} registros marcados como expirados.")
    except Exception as e:
        logger.error(f"Error en backup_retention_task: {str(e)}")
    finally:
        db.close()

def retention_policy_task():
    """Tarea para limpiar datos de monitoreo de más de 30 días."""
    db = SessionLocal()
    try:
        logger.info("Ejecutando política de retención (Limpieza de datos > 30 días)...")
        result = purge_old_monitoring_data(db, days=30)
        logger.info(f"Limpieza completada: {result['deleted_metrics']} métricas y {result['deleted_sessions']} sesiones eliminadas.")
    except Exception as e:
        logger.error(f"Error en política de retención: {str(e)}")
    finally:
        db.close()

def monitor_ssh_task(servidor_id: int, credencial_id: int):
    """Tarea individual para monitoreo SSH."""
    db = SessionLocal()
    try:
        logger.info(f"Iniciando monitoreo SSH para Servidor ID: {servidor_id}")
        run_ssh_monitoring(db, servidor_id, credencial_id)
    except Exception as e:
        logger.error(f"Error en monitoreo SSH (Srv: {servidor_id}): {str(e)}")
    finally:
        db.close()

def safe_get(obj, attr, default=0):
    """Obtiene de forma segura un atributo de un objeto Pydantic, dict o modelo regular."""
    if obj is None:
        return default
    if isinstance(obj, dict):
        return obj.get(attr, default)
    if hasattr(obj, 'model_dump'):
        try:
            return obj.model_dump().get(attr, default)
        except Exception:
            pass
    if hasattr(obj, 'dict'):
        try:
            return obj.dict().get(attr, default)
        except Exception:
            pass
    if hasattr(obj, '__dict__'):
        return getattr(obj, attr, default)
    try:
        return getattr(obj, attr, default)
    except AttributeError:
        return default

def monitor_db_task(instancia_id: int, credencial_id: int):
    """
    Tarea individual para monitoreo de base de datos.
    Ejecutada de forma asíncrona e independiente con su propia sesión.
    """
    db = SessionLocal()
    try:
        instancia = db.query(InstanciaDBMS).filter(InstanciaDBMS.id_instancia == instancia_id).first()
        if not instancia:
            logger.error(f"Instancia DBMS con ID {instancia_id} no encontrada.")
            return
            
        servidor = instancia.servidor
        if not servidor:
            logger.error(f"Servidor no asociado a la instancia ID {instancia_id}.")
            return
            
        dbms_id = instancia.id_dbms
        
        # 1. Ejecutar colector modular correspondiente
        metrics_result = None
        if dbms_id == 2:  # MySQL 5
            metrics_result = run_mysql5_modular_monitoring(db, instancia_id, credencial_id)
        elif dbms_id == 3:  # MySQL 8
            metrics_result = run_mysql8_modular_monitoring(db, instancia_id, credencial_id)
        elif dbms_id == 4:  # Oracle
            metrics_result = run_oracle_modular_monitoring(db, instancia_id, credencial_id)
        elif dbms_id == 5:  # MongoDB
            metrics_result = run_mongodb_modular_monitoring(db, instancia_id, credencial_id)
            
        if not metrics_result or "error" in metrics_result:
            error_msg = metrics_result.get("error") if metrics_result else "Resultado de recolección vacío."
            logger.error(f"Error recolectando métricas para instancia ID {instancia_id}: {error_msg}")
            
            # Persistir Monitoreo fallido y Alerta
            nuevo_monitoreo = Monitoreo(id_servidor=servidor.id_servidor, id_estado_monitoreo=5, fecha_fin=datetime.now())
            db.add(nuevo_monitoreo)
            db.commit()
            db.refresh(nuevo_monitoreo)
            
            db.add(Alerta(
                descripcion=f"Instancia {instancia.nombre_instancia} NO RESPONDE (Fallo en monitoreo modular: {error_msg})",
                id_servidor=servidor.id_servidor,
                id_monitoreo=nuevo_monitoreo.id_monitoreo,
                id_nivel_alerta=4, # Fatal
                id_estado_alerta=6  # Activo
            ))
            db.commit()
            
            # Registrar en LIVE_DB_CACHE como offline (piped comprimido)
            timestamp = int(datetime.now(timezone.utc).timestamp())
            LIVE_DB_CACHE[instancia_id] = f"offline|0|0|0|0.0|0|0|0.0|0|0|0|0|0|100.0|{timestamp}"
            return

        # 2. Descomprimir grupos de métricas
        grupo_a = metrics_result.get("grupo_a")
        grupo_b = metrics_result.get("grupo_b")
        grupo_c = metrics_result.get("grupo_c")
        
        status = safe_get(grupo_a, "status", "offline")
        uptime = int(safe_get(grupo_a, "uptime", 0))
        threads_conn = int(safe_get(grupo_a, "threads_connected", 0))
        max_conn = int(safe_get(grupo_a, "max_connections", 151))
        conn_usage = float(safe_get(grupo_a, "connection_usage_percent", 0.0))
        
        # Grupo B (Recursos) - Opcional
        threads_run = int(safe_get(grupo_b, "threads_running", 0)) if grupo_b else 0
        questions = int(safe_get(grupo_b, "questions", 0)) if grupo_b else 0
        qps = float(safe_get(grupo_b, "queries_per_second", 0.0)) if grupo_b else 0.0
        slow = int(safe_get(grupo_b, "slow_queries", 0)) if grupo_b else 0
        locks = int(safe_get(grupo_b, "table_locks_waited", 0)) if grupo_b else 0
        
        # Grupo C (Desempeño) - Opcional
        row_locks = int(safe_get(grupo_c, "innodb_row_lock_waits", 0)) if grupo_c else 0
        lock_time = int(safe_get(grupo_c, "innodb_row_lock_time_avg", 0)) if grupo_c else 0
        dirty = int(safe_get(grupo_c, "innodb_buffer_pool_pages_dirty", 0)) if grupo_c else 0
        hit_ratio = float(safe_get(grupo_c, "innodb_buffer_pool_hit_ratio", 100.0)) if grupo_c else 100.0
        
        timestamp = int(datetime.now(timezone.utc).timestamp())
        
        # 3. Guardar en el Caché Global en formato piped comprimido
        LIVE_DB_CACHE[instancia_id] = (
            f"{status}|{uptime}|{threads_conn}|{max_conn}|{conn_usage}|"
            f"{threads_run}|{questions}|{qps}|{slow}|{locks}|"
            f"{row_locks}|{lock_time}|{dirty}|{hit_ratio}|{timestamp}"
        )
        
        # 4. Registrar sesión de monitoreo exitosa
        nuevo_monitoreo = Monitoreo(id_servidor=servidor.id_servidor, id_estado_monitoreo=4, fecha_fin=datetime.now())
        db.add(nuevo_monitoreo)
        db.commit()
        db.refresh(nuevo_monitoreo)
        
        # 5. Persistencia Inteligente por Umbrales
        if conn_usage >= 90.0:
            tipo = db.query(TipoMetrica).filter(TipoMetrica.nombre_tipo == "DB_Capacity").first()
            if not tipo:
                tipo = TipoMetrica(nombre_tipo="DB_Capacity", unidad_medida="%")
                db.add(tipo)
                db.commit()
                db.refresh(tipo)
                
            db.add(Metrica(
                valor=conn_usage,
                id_monitoreo=nuevo_monitoreo.id_monitoreo,
                id_tipo_metrica=tipo.id_tipo_metrica
            ))
            
            db.add(Alerta(
                descripcion=f"Capacidad de conexiones crítica en {instancia.nombre_instancia}: {conn_usage}%",
                id_servidor=servidor.id_servidor,
                id_monitoreo=nuevo_monitoreo.id_monitoreo,
                id_nivel_alerta=3, # Crítico
                id_estado_alerta=6  # Activo
            ))
            db.commit()
            
        if status == "offline":
            db.add(Alerta(
                descripcion=f"Instancia {instancia.nombre_instancia} NO RESPONDE (Ping fallido)",
                id_servidor=servidor.id_servidor,
                id_monitoreo=nuevo_monitoreo.id_monitoreo,
                id_nivel_alerta=4, # Fatal
                id_estado_alerta=6  # Activo
            ))
            db.commit()
            
    except Exception as e:
        logger.error(f"Error en monitor_db_task para Instancia ID {instancia_id}: {str(e)}")
    finally:
        db.close()

def bulk_monitor_by_criticality(nivel_criticidad_id: int):
    """
    Orquestador masivo: Busca todos los activos de un nivel y los manda al pool.
    SOLO monitorea servidores que ya existan en la tabla Monitoreo (Lista Blanca).
    Respeta los flags monitoreo_host y monitoreo_db.
    """
    db = SessionLocal()
    try:
        # 1. Monitoreo SSH (HARDWARE)
        servidores = db.query(Servidor).filter(
            Servidor.id_nivel_criticidad == nivel_criticidad_id,
            Servidor.id_estado_servidor == 1, # Activo en CMDB
            Servidor.monitoreo_host == True,  # <--- Solo si tiene activo el monitoreo de host
            db.query(Monitoreo).filter(Monitoreo.id_servidor == Servidor.id_servidor).exists()
        ).all()

        if servidores:
            for srv in servidores:
                # Buscar credencial SSH activa (id_tipo_acceso = 1)
                cred = db.query(CredencialAcceso).filter(
                    CredencialAcceso.id_servidor == srv.id_servidor,
                    CredencialAcceso.id_tipo_acceso == 1,
                    CredencialAcceso.id_estado_credencial == 1
                ).first()
                
                if cred:
                    from app.core.scheduler_manager import scheduler_executor
                    scheduler_executor.submit(monitor_ssh_task, srv.id_servidor, cred.id_credencial)
                else:
                    logger.warning(f"Servidor {srv.direccion_ip} no tiene credencial SSH activa.")
        else:
            logger.info(f"No hay servidores para monitoreo de HOST en criticidad ID: {nivel_criticidad_id}")

        # 2. Monitoreo UNIFICADO de RDBMS (BASE DE DATOS)
        instancias = db.query(InstanciaDBMS).join(Servidor).filter(
            Servidor.id_nivel_criticidad == nivel_criticidad_id,
            Servidor.monitoreo_db == True,     # <--- Solo si tiene activo el monitoreo de DB
            InstanciaDBMS.id_estado_instancia == 1 # Activa
        ).all()

        for inst in instancias:
            # Buscar credencial DB Native activa (id_tipo_acceso = 2)
            cred_db = db.query(CredencialAcceso).filter(
                CredencialAcceso.id_servidor == inst.id_servidor,
                CredencialAcceso.id_tipo_acceso == 2,
                CredencialAcceso.id_estado_credencial == 1
            ).first()

            if cred_db:
                from app.core.scheduler_manager import scheduler_executor
                scheduler_executor.submit(monitor_db_task, inst.id_instancia, cred_db.id_credencial)

    except Exception as e:
        logger.error(f"Error en bulk_monitor: {str(e)}")
    finally:
        db.close()
