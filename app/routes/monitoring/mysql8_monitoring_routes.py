from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.db.postgres.postgres_connection import get_db as get_pg_db
from app.services.monitoring.mysql8.mysql8_service import get_mysql8_metrics, run_mysql8_modular_monitoring
from app.core.dynamic_db_core import get_dynamic_session
from app.services import get_servidor, get_credencial
from app.schemas import MySQL8Metrics, MySQLModularMonitoringResponse
from app.core.dependencies import get_current_user

router = APIRouter(dependencies=[Depends(get_current_user)])

@router.get("/{servidor_id}/{credencial_id}", response_model=MySQL8Metrics)
def monitor_mysql8(servidor_id: int, credencial_id: int, db: Session = Depends(get_pg_db)):
    """Realiza monitoreo en tiempo real de MySQL 8."""
    servidor = get_servidor(db, servidor_id)
    credencial = get_credencial(db, credencial_id)
    
    if not servidor or not credencial:
        raise HTTPException(status_code=404, detail="Servidor o credencial no encontrados")
    
    try:
        remote_db = get_dynamic_session(servidor, credencial, dbms_id=3) # 3: MySQL 8
        metrics = get_mysql8_metrics(remote_db)
        return metrics
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if 'remote_db' in locals(): remote_db.close()

@router.get("/modular/{id_instancia}/{id_credencial}", response_model=MySQLModularMonitoringResponse)
def get_mysql8_modular_metrics(id_instancia: int, id_credencial: int, db: Session = Depends(get_pg_db)):
    """
    Obtiene métricas de MySQL 8 segmentadas por módulos (A, B, C) 
    según el nivel de criticidad del servidor registrado.
    """
    result = run_mysql8_modular_monitoring(db, id_instancia, id_credencial)
    
    if "error" in result:
        raise HTTPException(status_code=500, detail=result["error"])
        
    return result

