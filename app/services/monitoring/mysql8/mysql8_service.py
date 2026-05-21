from sqlalchemy.orm import Session
from datetime import datetime
from app.models.infrastructure_models import InstanciaDBMS, NivelCriticidad
from app.core.dynamic_db_core import get_dynamic_session
from app.services import get_credencial
from app.services.monitoring.mysql8.metrics.connectivity_provider import get_group_a_connectivity
from app.services.monitoring.mysql8.metrics.resource_provider import get_group_b_resources
from app.services.monitoring.mysql8.metrics.performance_provider import get_group_c_performance
from app.schemas import MySQL8Metrics
from app.services.monitoring.mysql5.mysql5_service import get_mysql5_metrics

def get_mysql8_metrics(db: Session) -> MySQL8Metrics:
    """
    Extrae métricas de rendimiento de un servidor MySQL 8.
    Reutiliza la lógica base de MySQL 5 ya que los comandos SHOW GLOBAL STATUS son compatibles.
    """
    m5_data = get_mysql5_metrics(db)
    return MySQL8Metrics(**m5_data.model_dump())

def run_mysql8_modular_monitoring(db: Session, id_instancia: int, id_credencial: int) -> dict:
    """
    Orquesta la recolección de métricas modulares de MySQL 8 de acuerdo a la criticidad del servidor.
    """
    # 1. Obtener Instancia y Servidor
    instancia = db.query(InstanciaDBMS).filter(InstanciaDBMS.id_instancia == id_instancia).first()
    if not instancia:
        return {"error": "Instancia MySQL 8 no encontrada"}
        
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
        # Conexión dinámica (conectamos a 'performance_schema' en MySQL 8 para asegurar que esté en contexto)
        remote_session = get_dynamic_session(servidor, credencial, dbms_id=3, db_name="performance_schema")
        
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
        return {"error": f"Fallo en monitoreo modular MySQL 8: {str(e)}"}
    finally:
        if remote_session:
            remote_session.close()
