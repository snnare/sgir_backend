from pymongo import MongoClient
from sqlalchemy.orm import Session
from datetime import datetime
from app.models.infrastructure_models import InstanciaDBMS, NivelCriticidad
from app.core.dynamic_db_core import get_dynamic_session
from app.services import get_credencial
from app.services.monitoring.mongodb.metrics.connectivity_provider import get_group_a_connectivity
from app.services.monitoring.mongodb.metrics.resource_provider import get_group_b_resources
from app.services.monitoring.mongodb.metrics.performance_provider import get_group_c_performance
from app.schemas import MongoDBMetrics

def get_mongodb_metrics(client: MongoClient) -> MongoDBMetrics:
    """
    Extrae métricas de rendimiento de un servidor MongoDB usando serverStatus.
    """
    try:
        # Comando administrativo para obtener el estado del servidor
        status_data = client.admin.command("serverStatus")
        
        return MongoDBMetrics(
            status="online",
            uptime=int(status_data.get("uptime", 0)),
            connections_current=int(status_data["connections"].get("current", 0)),
            connections_available=int(status_data["connections"].get("available", 0)),
            connections_total_created=int(status_data["connections"].get("totalCreated", 0)),
            op_inserts=int(status_data["opcounters"].get("insert", 0)),
            op_queries=int(status_data["opcounters"].get("query", 0)),
            op_updates=int(status_data["opcounters"].get("update", 0)),
            op_deletes=int(status_data["opcounters"].get("delete", 0)),
            mem_resident_mb=int(status_data["mem"].get("resident", 0)),
            mem_virtual_mb=int(status_data["mem"].get("virtual", 0)),
            ok=float(status_data.get("ok", 0.0))
        )
    except Exception:
        return MongoDBMetrics(
            status="offline", uptime=0, connections_current=0, connections_available=0,
            connections_total_created=0, op_inserts=0, op_queries=0, op_updates=0,
            op_deletes=0, mem_resident_mb=0, mem_virtual_mb=0, ok=0.0
        )

def list_databases_discovery(client: MongoClient) -> list[dict]:
    """
    Lista todas las bases de datos en MongoDB y su tamaño en disco.
    """
    db_info = client.admin.command("listDatabases")
    databases = db_info.get("databases", [])
    
    return [
        {
            "nombre": db["name"], 
            "tamano_mb": round(float(db["sizeOnDisk"] / 1024 / 1024), 2)
        } 
        for db in databases if db["name"] not in ["admin", "config", "local"]
    ]

def run_mongodb_modular_monitoring(db: Session, id_instancia: int, id_credencial: int) -> dict:
    """
    Orquesta la recolección de métricas modulares de MongoDB de acuerdo a la criticidad del servidor.
    """
    # 1. Obtener Instancia y Servidor
    instancia = db.query(InstanciaDBMS).filter(InstanciaDBMS.id_instancia == id_instancia).first()
    if not instancia:
        return {"error": "Instancia MongoDB no encontrada"}
        
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

    client = None
    try:
        # Conexión dinámica (dbms_id = 5 para MongoDB)
        client = get_dynamic_session(
            servidor, 
            credencial, 
            dbms_id=5, 
            parametros=instancia.parametros_conexion
        )
        
        timestamp = datetime.now()

        # Grupo A (Siempre)
        grupo_a = get_group_a_connectivity(client)
        
        grupo_b = None
        if criticidad_id >= 2 and grupo_a.status == "online": # Medio, Alto, Crítico
            grupo_b = get_group_b_resources(client)

        grupo_c = None
        if criticidad_id >= 3 and grupo_a.status == "online": # Alto, Crítico
            grupo_c = get_group_c_performance(client)

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
        return {"error": f"Fallo en monitoreo modular MongoDB: {str(e)}"}
