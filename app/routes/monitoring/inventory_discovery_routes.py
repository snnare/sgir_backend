from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.db.postgres.postgres_connection import get_db as get_pg_db
from app.services.inventory_sync_service import sync_databases_inventory
from app.core.dependencies import get_current_user
from app.services.infrastructure_crud import get_servidor, get_instancia
from sqlalchemy import func
from app.models.infrastructure_models import BaseDeDatos

router = APIRouter(dependencies=[Depends(get_current_user)])

@router.post("/sync/{instancia_id}")
def trigger_sync(instancia_id: int, db: Session = Depends(get_pg_db)):
    """
    Sincroniza el inventario de bases de datos para una instancia específica.
    Actualiza la tabla Base_de_Datos con nombres y tamaños reales.
    """
    result = sync_databases_inventory(db, instancia_id)
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    return result

@router.get("/summary/{servidor_id}")
def get_server_storage_summary(servidor_id: int, db: Session = Depends(get_pg_db)):
    """
    Consulta rápida (local) de cuántas bases de datos y el peso total en un servidor.
    """
    # 1. Obtener todas las instancias del servidor
    instancias = db.query(BaseDeDatos.id_instancia).join(
        BaseDeDatos.instancia
    ).filter(BaseDeDatos.instancia.has(id_servidor=servidor_id), BaseDeDatos.id_estado_bd == 1).subquery()

    # 2. Sumar
    summary = db.query(
        func.count(BaseDeDatos.id_base_datos).label("total_dbs"),
        func.sum(BaseDeDatos.tamano_mb).label("total_size_mb")
    ).filter(BaseDeDatos.id_instancia.in_(instancias)).first()

    return {
        "servidor_id": servidor_id,
        "total_databases": summary.total_dbs or 0,
        "total_size_mb": float(summary.total_size_mb or 0)
    }
