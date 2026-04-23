from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.db.postgres.postgres_connection import get_db as get_pg_db
from app.services.monitoring.oracle.oracle_monitoring_service import run_oracle_modular_monitoring
from app.schemas.catalogs.monitoring_persistence_schemas import OracleMonitoringResponse
from app.core.dependencies import get_current_user

router = APIRouter(dependencies=[Depends(get_current_user)])

@router.get("/{id_instancia}/{id_credencial}", response_model=OracleMonitoringResponse)
def get_oracle_modular_metrics(id_instancia: int, id_credencial: int, db: Session = Depends(get_pg_db)):
    """
    Obtiene métricas de Oracle segmentadas por módulos (A, B, C) 
    según el nivel de criticidad del servidor registrado.
    """
    result = run_oracle_modular_monitoring(db, id_instancia, id_credencial)
    
    if "error" in result:
        raise HTTPException(status_code=500, detail=result["error"])
        
    return result
