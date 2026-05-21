from fastapi import APIRouter
from .mysql5_monitoring_routes import router as mysql5_router
from .mysql8_monitoring_routes import router as mysql8_router
from .mongodb_monitoring_routes import router as mongodb_router
from .oracle_monitoring_routes import router as oracle_router
from .inventory_discovery_routes import m2_router as inventory_m2_router, m3_router as inventory_m3_router
from .host_monitoring_routes import m1_router as host_m1_router, m2_router as host_m2_router, m3_router as host_m3_router
from .db_monitoring_routes import router as db_router

m1_router = APIRouter(prefix="/m1")
m2_router = APIRouter(prefix="/m2")
m3_router = APIRouter(prefix="/m3")

# Módulo 1 (Monitoreo)
m1_router.include_router(db_router, prefix="/db", tags=["Monitoring - Unified DB"])
m1_router.include_router(mysql5_router, prefix="/mysql5", tags=["Monitoring - MySQL 5"])
m1_router.include_router(mysql8_router, prefix="/mysql8", tags=["Monitoring - MySQL 8"])
m1_router.include_router(mongodb_router, prefix="/mongodb", tags=["Monitoring - MongoDB"])
m1_router.include_router(oracle_router, prefix="/oracle", tags=["Monitoring - Oracle"])
m1_router.include_router(host_m1_router, prefix="/host", tags=["Monitoring - SSH Host"])

# Módulo 2 (Búsqueda de Activos - CMDB)
m2_router.include_router(host_m2_router, prefix="/host", tags=["Assets Discovery - SSH Host"])
m2_router.include_router(inventory_m2_router, prefix="/inventory", tags=["Assets Discovery - Inventory"])

# Módulo 3 (Gestión de Respaldos)
m3_router.include_router(host_m3_router, prefix="/host", tags=["Backups - SSH Host"])
m3_router.include_router(inventory_m3_router, prefix="/inventory", tags=["Backups - Inventory"])

__all__ = [
    "m1_router",
    "m2_router",
    "m3_router"
]
