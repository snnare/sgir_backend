from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.db.postgres.postgres_connection import get_db as get_pg_db
from app.services.monitoring.mongodb.mongodb_service import get_mongodb_metrics
from app.core.dynamic_db_core import get_dynamic_session
from app.services import get_servidor, get_credencial
from app.schemas import MongoDBMetrics
from app.core.dependencies import get_current_user

router = APIRouter(dependencies=[Depends(get_current_user)])

@router.get("/{servidor_id}/{credencial_id}", response_model=MongoDBMetrics)
def monitor_mongodb(servidor_id: int, credencial_id: int, db: Session = Depends(get_pg_db)):
    """Realiza monitoreo en tiempo real de MongoDB."""
    servidor = get_servidor(db, servidor_id)
    credencial = get_credencial(db, credencial_id)
    
    if not servidor or not credencial:
        raise HTTPException(status_code=404, detail="Servidor o credencial no encontrados")
    
    try:
        # Para Mongo, get_dynamic_session devuelve un MongoClient
        client = get_dynamic_session(servidor, credencial, dbms_id=5) # 5: Mongo
        metrics = get_mongodb_metrics(client)
        return metrics
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if 'client' in locals(): client.close()
