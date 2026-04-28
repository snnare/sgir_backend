from sqlalchemy.orm import Session
from app.db.postgres.postgres_connection import SessionLocal
from app.models.infrastructure_models import Servidor, InstanciaDBMS, CredencialAcceso
from app.services.monitoring.ssh_service import run_ssh_monitoring
from app.models.monitoring_persistence_models import Monitoreo, Metrica, TipoMetrica
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("scheduler_tasks")

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

def bulk_monitor_by_criticality(nivel_criticidad_id: int):
    """
    Orquestador masivo: Busca todos los activos de un nivel y los manda al pool.
    Limitado exclusivamente a monitoreo SSH por requerimiento.
    """
    db = SessionLocal()
    try:
        # 1. Monitoreo SSH
        servidores = db.query(Servidor).filter(
            Servidor.id_nivel_criticidad == nivel_criticidad_id,
            Servidor.id_estado_servidor == 1 # Activo
        ).all()

        if not servidores:
            logger.info(f"No hay servidores activos para criticidad ID: {nivel_criticidad_id}")
            return

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

    except Exception as e:
        logger.error(f"Error en bulk_monitor: {str(e)}")
    finally:
        db.close()
