from fastapi import APIRouter
from .mysql5_monitoring_routes import router as mysql5_router
from .mysql8_monitoring_routes import router as mysql8_router
from .mongodb_monitoring_routes import router as mongodb_router
from .inventory_discovery_routes import router as inventory_router

router = APIRouter()

router.include_router(mysql5_router, prefix="/mysql5", tags=["Monitoring - MySQL 5"])
router.include_router(mysql8_router, prefix="/mysql8", tags=["Monitoring - MySQL 8"])
router.include_router(mongodb_router, prefix="/mongodb", tags=["Monitoring - MongoDB"])
router.include_router(inventory_router, prefix="/inventory", tags=["Monitoring - Inventory Discovery"])
