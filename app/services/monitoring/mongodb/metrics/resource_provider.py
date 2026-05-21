from pymongo import MongoClient
from app.schemas import MongoResourceMetrics

def get_group_b_resources(client: MongoClient) -> MongoResourceMetrics:
    """
    Grupo B: Conexiones y Memoria RAM de MongoDB.
    """
    try:
        status_data = client.admin.command("serverStatus")
        
        connections_current = int(status_data["connections"].get("current", 0))
        connections_available = int(status_data["connections"].get("available", 0))
        connections_total_created = int(status_data["connections"].get("totalCreated", 0))
        mem_resident_mb = int(status_data["mem"].get("resident", 0))
        mem_virtual_mb = int(status_data["mem"].get("virtual", 0))

        return MongoResourceMetrics(
            connections_current=connections_current,
            connections_available=connections_available,
            connections_total_created=connections_total_created,
            mem_resident_mb=mem_resident_mb,
            mem_virtual_mb=mem_virtual_mb
        )
    except Exception:
        return MongoResourceMetrics(
            connections_current=0,
            connections_available=0,
            connections_total_created=0,
            mem_resident_mb=0,
            mem_virtual_mb=0
        )
