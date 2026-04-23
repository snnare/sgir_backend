from sqlalchemy.orm import Session
from datetime import datetime
from app.core.dynamic_db_core import get_dynamic_session
from app.models.infrastructure_models import InstanciaDBMS
from app.services.monitoring.oracle.metrics.connectivity_provider import get_group_a_connectivity
from app.services.monitoring.oracle.metrics.resource_provider import get_group_b_resources
from app.services.monitoring.oracle.metrics.performance_provider import get_group_c_performance

def run_oracle_modular_monitoring(db: Session, id_instancia: int, id_credencial: int) -> dict:
    # 1. Obtener Metadatos del Servidor e Instancia
    instancia = db.query(InstanciaDBMS).filter(InstanciaDBMS.id_instancia == id_instancia).first()
    if not instancia:
        return {"error": "Instancia no encontrada"}
    
    servidor = instancia.servidor
    criticidad_id = servidor.id_nivel_criticidad # 1: Bajo, 2: Medio, 3: Alto, 4: Crítico
    
    # Obtener el nombre del nivel de criticidad manualmente para evitar problemas de relación
    from app.models.infrastructure_models import NivelCriticidad
    criticidad_obj = db.query(NivelCriticidad).filter(NivelCriticidad.id_nivel_criticidad == criticidad_id).first()
    criticidad_nombre = criticidad_obj.nombre_nivel if criticidad_obj else "Desconocido"
    
    # 2. Conexión Dinámica a Oracle
    # Reutilizamos la credencial pasada por el endpoint
    from app.services import get_credencial
    credencial = get_credencial(db, id_credencial)
    
    remote_session = None
    try:
        remote_session = get_dynamic_session(servidor, credencial, dbms_id=4, db_name=instancia.nombre_instancia)
        
        # 3. Recolección Modular basada en Criticidad
        timestamp = datetime.now()
        
        # Grupo A (Siempre se ejecuta)
        grupo_a = get_group_a_connectivity(remote_session)
        
        grupo_b = None
        if criticidad_id >= 2: # Medio, Alto, Crítico
            grupo_b = get_group_b_resources(remote_session)
            
        grupo_c = None
        if criticidad_id >= 3: # Alto, Crítico
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
        return {"error": f"Fallo en monitoreo modular Oracle: {str(e)}"}
    finally:
        if remote_session:
            remote_session.close()
