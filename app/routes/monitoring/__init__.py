from fastapi import APIRouter
from .mysql5_monitoring_routes import router as mysql5_router

router = APIRouter()

router.include_router(mysql5_router, prefix="/mysql5", tags=["Monitoring - MySQL 5"])
