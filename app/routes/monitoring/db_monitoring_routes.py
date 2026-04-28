from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.db.postgres.postgres_connection import get_db
from app.core.dependencies import get_current_user
from app.services.monitoring.db_unified_service import get_db_health_status, run_unified_db_monitoring

router = APIRouter()

@router.get("/health-status/{instancia_id}")
def check_db_health(instancia_id: int, db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    """Consulta el estado unificado de salud de cualquier motor (Oracle, MySQL, Mongo)."""
    return get_db_health_status(db, instancia_id)

@router.post("/run-adhoc/{instancia_id}/{credencial_id}")
def run_adhoc_db_monitor(instancia_id: int, credencial_id: int, db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    """Dispara un monitoreo manual instantáneo."""
    return run_unified_db_monitoring(db, instancia_id, credencial_id)
