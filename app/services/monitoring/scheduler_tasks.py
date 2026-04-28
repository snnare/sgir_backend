from sqlalchemy.orm import Session
from app.db.postgres.postgres_connection import SessionLocal
from app.models.infrastructure_models import Servidor, InstanciaDBMS, CredencialAcceso
from app.services.monitoring.ssh_service import run_ssh_monitoring
from app.core.dynamic_db_core import get_dynamic_session
from app.models.monitoring_persistence_models import Monitoreo, Metrica, TipoMetrica
from app.models.infrastructure_models import DBMS
from app.models.monitoring_persistence_models import Alerta
from sqlalchemy import text
from datetime import datetime
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("scheduler_tasks")

def get_db():
    db = SessionLocal()
    try:
        yield db
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

def monitor_rdbms_task(instancia_id: int, credencial_id: int):
    """Tarea individual para monitoreo de salud RDBMS."""
    db = SessionLocal()
    try:
        instancia = db.query(InstanciaDBMS).filter(InstanciaDBMS.id_instancia == instancia_id).first()
        if not instancia: return

        servidor = instancia.servidor
        credencial = db.query(CredencialAcceso).filter(CredencialAcceso.id_credencial == credencial_id).first()

        # Iniciar sesión de monitoreo
        nuevo_monitoreo = Monitoreo(
            id_servidor=servidor.id_servidor,
            id_credencial=credencial_id,
            id_estado_monitoreo=1 # Activo
        )
        db.add(nuevo_monitoreo)
        db.commit()
        db.refresh(nuevo_monitoreo)

        try:
            # Test de Conectividad
            session = get_dynamic_session(servidor, credencial, instancia.id_dbms, db_name=instancia.nombre_instancia)
            
            # Query de salud básica según motor
            query = text("SELECT 1")
            if instancia.id_dbms == 4: # Oracle
                query = text("SELECT 1 FROM DUAL")
            
            session.execute(query)
            session.close()

            # Registrar métrica de disponibilidad (Tipo 6: Disponibilidad si no existe)
            tipo_disponibilidad = db.query(TipoMetrica).filter(TipoMetrica.nombre_tipo == "Disponibilidad").first()
            if not tipo_disponibilidad:
                tipo_disponibilidad = TipoMetrica(nombre_tipo="Disponibilidad", unidad_medida="Boolean")
                db.add(tipo_disponibilidad)
                db.commit()
                db.refresh(tipo_disponibilidad)

            db.add(Metrica(
                valor=1,
                id_monitoreo=nuevo_monitoreo.id_monitoreo,
                id_tipo_metrica=tipo_disponibilidad.id_tipo_metrica
            ))
            
            nuevo_monitoreo.id_estado_monitoreo = 4 # Éxito
            logger.info(f"Monitoreo RDBMS Exitoso: Instancia {instancia.nombre_instancia}")

        except Exception as db_err:
            nuevo_monitoreo.id_estado_monitoreo = 5 # Fallo
            # Crear Alerta Automática
            nueva_alerta = Alerta(
                descripcion=f"Fallo de conectividad en instancia {instancia.nombre_instancia}: {str(db_err)}",
                id_servidor=servidor.id_servidor,
                id_monitoreo=nuevo_monitoreo.id_monitoreo,
                id_nivel_alerta=3, # Crítico
                id_estado_alerta=6 # Abierta
            )
            db.add(nueva_alerta)
            logger.error(f"Fallo RDBMS en {instancia.nombre_instancia}: {str(db_err)}")

        nuevo_monitoreo.fecha_fin = datetime.now()
        db.commit()

    except Exception as e:
        logger.error(f"Error crítico en tarea RDBMS: {str(e)}")
    finally:
        db.close()

def bulk_monitor_by_criticality(nivel_criticidad_id: int):
    """
    Orquestador masivo: Busca todos los activos de un nivel y los manda al pool.
    """
    db = SessionLocal()
    try:
        # 1. Monitoreo SSH
        servidores = db.query(Servidor).filter(
            Servidor.id_nivel_criticidad == nivel_criticidad_id,
            Servidor.id_estado_servidor == 1 # Activo
        ).all()

        for srv in servidores:
            # Buscar credencial SSH activa
            cred = db.query(CredencialAcceso).filter(
                CredencialAcceso.id_servidor == srv.id_servidor,
                CredencialAcceso.id_tipo_acceso == 1,
                CredencialAcceso.id_estado_credencial == 1
            ).first()
            
            if cred:
                # Aquí el scheduler_manager se encargará de ejecutarlo en un hilo
                from app.core.scheduler_manager import scheduler_executor
                scheduler_executor.submit(monitor_ssh_task, srv.id_servidor, cred.id_credencial)

        # 2. Monitoreo RDBMS
        instancias = db.query(InstanciaDBMS).join(Servidor).filter(
            Servidor.id_nivel_criticidad == nivel_criticidad_id,
            InstanciaDBMS.id_estado_instancia == 1
        ).all()

        for inst in instancias:
            # Buscar credencial DB Native activa
            cred = db.query(CredencialAcceso).filter(
                CredencialAcceso.id_servidor == inst.id_servidor,
                CredencialAcceso.id_tipo_acceso == 2,
                CredencialAcceso.id_estado_credencial == 1
            ).first()

            if cred:
                from app.core.scheduler_manager import scheduler_executor
                scheduler_executor.submit(monitor_rdbms_task, inst.id_instancia, cred.id_credencial)

    finally:
        db.close()
