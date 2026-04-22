from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.db.postgres.postgres_connection import get_db as get_pg_db
from app.services.monitoring.mysql5.mysql5_service import get_mysql5_metrics
from app.core.dynamic_db_core import get_dynamic_session
from app.services import get_servidor, get_credencial
from app.schemas import MySQL5Metrics
from app.core.dependencies import get_current_user

router = APIRouter(dependencies=[Depends(get_current_user)])

@router.get("/{servidor_id}/{credencial_id}", response_model=MySQL5Metrics)
def monitor_mysql5(servidor_id: int, credencial_id: int, db: Session = Depends(get_pg_db)):
    """
    Realiza un monitoreo en tiempo real de una instancia MySQL 5 remota.
    """
    servidor = get_servidor(db, servidor_id)
    credencial = get_credencial(db, credencial_id)
    
    if not servidor or not credencial:
        raise HTTPException(status_code=404, detail="Servidor o credencial no encontrados")
    
    # 1. Crear sesión dinámica
    try:
        remote_db = get_dynamic_session(servidor, credencial)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al conectar al servidor remoto: {str(e)}")
    
    # 2. Extraer métricas
    try:
        metrics = get_mysql5_metrics(remote_db)
        return metrics
    finally:
        remote_db.close()
