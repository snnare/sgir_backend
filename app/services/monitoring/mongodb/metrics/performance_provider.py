from pymongo import MongoClient
from app.schemas import MongoPerformanceMetrics

def get_group_c_performance(client: MongoClient) -> MongoPerformanceMetrics:
    """
    Grupo C: Rendimiento de Operaciones (Opcounters) de MongoDB.
    """
    try:
        status_data = client.admin.command("serverStatus")
        
        op_inserts = int(status_data["opcounters"].get("insert", 0))
        op_queries = int(status_data["opcounters"].get("query", 0))
        op_updates = int(status_data["opcounters"].get("update", 0))
        op_deletes = int(status_data["opcounters"].get("delete", 0))

        return MongoPerformanceMetrics(
            op_inserts=op_inserts,
            op_queries=op_queries,
            op_updates=op_updates,
            op_deletes=op_deletes
        )
    except Exception:
        return MongoPerformanceMetrics(
            op_inserts=0,
            op_queries=0,
            op_updates=0,
            op_deletes=0
        )
