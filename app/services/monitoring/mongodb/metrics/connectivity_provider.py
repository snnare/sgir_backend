from pymongo import MongoClient
from app.schemas import MongoConnectivityMetrics

def get_group_a_connectivity(client: MongoClient) -> MongoConnectivityMetrics:
    """
    Grupo A: Conectividad y Salud Básica de MongoDB.
    """
    try:
        # Ping
        ping_res = client.admin.command("ping")
        ok = float(ping_res.get("ok", 0.0))
        status = "online" if ok == 1.0 else "offline"

        # Uptime
        status_data = client.admin.command("serverStatus")
        uptime = int(status_data.get("uptime", 0))

        return MongoConnectivityMetrics(
            status=status,
            uptime=uptime,
            ok=ok
        )
    except Exception:
        return MongoConnectivityMetrics(
            status="offline",
            uptime=0,
            ok=0.0
        )
