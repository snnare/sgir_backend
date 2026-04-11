from pymongo import MongoClient
from app.schemas.monitoring_persistence_schemas import MongoDBMetrics

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
