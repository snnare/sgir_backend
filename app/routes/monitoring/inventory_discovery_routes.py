from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.db.postgres.postgres_connection import get_db as get_pg_db
from app.services import sync_databases_inventory
from app.core.dependencies import get_current_user
from app.models.user_models import User
from sqlalchemy import func
from app.models.infrastructure_models import BaseDeDatos

router = APIRouter(dependencies=[Depends(get_current_user)])

@router.post("/discover/{instancia_id}/{credencial_id}")
def discover_and_sync(instancia_id: int, credencial_id: int, db: Session = Depends(get_pg_db), current_user: User = Depends(get_current_user)):
    """
    Inicia el proceso de auto-búsqueda en una instancia de base de datos.
    Sincroniza nombres, tamaños y fechas de creación en la CMDB.
    """
    result = sync_databases_inventory(db, instancia_id, credencial_id)
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    
    # Podríamos registrar un evento de auditoría aquí
    return result

@router.get("/summary/{servidor_id}")
def get_server_storage_summary(servidor_id: int, db: Session = Depends(get_pg_db)):
    """
    Consulta el estado actual del inventario local para un servidor.
    """
    summary = db.query(
        func.count(BaseDeDatos.id_base_datos).label("total_dbs"),
        func.sum(BaseDeDatos.tamano_mb).label("total_size_mb")
    ).join(BaseDeDatos.instancia).filter(
        BaseDeDatos.instancia.has(id_servidor=servidor_id),
        BaseDeDatos.id_estado_bd == 1
    ).first()

    return {
        "servidor_id": servidor_id,
        "total_databases": summary.total_dbs or 0,
        "total_size_mb": float(summary.total_size_mb or 0) if summary.total_size_mb else 0
    }
