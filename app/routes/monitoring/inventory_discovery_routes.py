from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from app.db.postgres.postgres_connection import get_db as get_pg_db
from app.services import sync_databases_inventory
from app.services.monitoring.ssh_service import (
    run_integrated_file_discovery, 
    run_server_integrated_file_discovery,
    run_custom_server_integrated_file_discovery
)
from app.core.dependencies import get_current_user
from app.models.user_models import User
from sqlalchemy import func
from app.models.infrastructure_models import BaseDeDatos
from app.services import infrastructure_crud
from app.schemas.infrastructure.infrastructure_schemas import GlobalAssetResponse
from typing import List

m2_router = APIRouter(dependencies=[Depends(get_current_user)])
m3_router = APIRouter(dependencies=[Depends(get_current_user)])

@m2_router.get("/assets", response_model=List[GlobalAssetResponse])
def get_global_assets(db: Session = Depends(get_pg_db)):
    """
    Retorna el inventario consolidado para la búsqueda de activos.
    """
    return infrastructure_crud.get_global_inventory(db)


@m2_router.post("/discover-all")
def discover_all_databases(db: Session = Depends(get_pg_db), current_user: User = Depends(get_current_user)):
    """
    Inicia un auto-descubrimiento masivo en todos los servidores con monitoreo_db activo.
    Sincroniza el inventario global y devuelve un resumen de almacenamiento.
    """
    from app.services.infrastructure.inventory_sync_service import run_bulk_inventory_sync
    return run_bulk_inventory_sync(db)

@m2_router.post("/discover/{instancia_id}/{credencial_id}")
def discover_and_sync(instancia_id: int, credencial_id: int, db: Session = Depends(get_pg_db), current_user: User = Depends(get_current_user)):
    """
    Inicia el proceso de auto-búsqueda en una instancia de base de datos.
    Sincroniza nombres, tamaños y fechas de creación en la CMDB.
    """
    result = sync_databases_inventory(db, instancia_id, credencial_id)
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    return result

@m3_router.post("/discover-backups/{instancia_id}/{credencial_id}/{ruta_id}")
def discover_integrated_backups(
    instancia_id: int, 
    credencial_id: int, 
    ruta_id: int,
    db: Session = Depends(get_pg_db),
    current_user: User = Depends(get_current_user)
):
    """
    Busca archivos físicos en el servidor y registra automáticamente
    las ejecuciones en la tabla Respaldo basándose en el DBMS y las BDs existentes.
    """
    result = run_integrated_file_discovery(db, instancia_id, credencial_id, ruta_id, current_user.id_usuario)
    if isinstance(result, dict) and "error" in result:
        raise HTTPException(status_code=404, detail=result["error"])
    return result

@m3_router.post("/discover-backups-server/{servidor_id}/{credencial_id}/{ruta_id}")
def discover_server_backups(
    servidor_id: int,
    credencial_id: int,
    ruta_id: int,
    db: Session = Depends(get_pg_db),
    current_user: User = Depends(get_current_user)
):
    """
    Busca archivos físicos en TODO el servidor (todas sus instancias) y registra 
    automáticamente las ejecuciones en la tabla Respaldo.
    """
    print(f"[DEBUG request] POST /sgir/v1/m3/inventory/discover-backups-server/{servidor_id}/{credencial_id}/{ruta_id}")
    result = run_server_integrated_file_discovery(db, servidor_id, credencial_id, ruta_id, current_user.id_usuario)
    print(f"[DEBUG discover_server_backups] Resultado del descubrimiento: {result}")
    if isinstance(result, list):
        print(f"[DEBUG discover_server_backups] Cantidad de elementos en el listado (tamaño del array): {len(result)}")
    if isinstance(result, dict) and "error" in result:
        raise HTTPException(status_code=404, detail=result["error"])
    return result

@m3_router.post("/discover-backups-custom/{servidor_id}/{credencial_id}/{ruta_id}")
def discover_custom_backups(
    servidor_id: int,
    credencial_id: int,
    ruta_id: int,
    days: int = Query(0, description="Días de antigüedad. 0 para cualquier fecha."),
    deep: bool = Query(True, description="True para búsqueda recursiva."),
    db: Session = Depends(get_pg_db),
    current_user: User = Depends(get_current_user)
):
    """
    Busca archivos físicos en TODO el servidor (todas sus instancias) con filtros
    personalizados de antigüedad (días) y búsqueda profunda (recursividad).
    """
    print(f"[DEBUG request] POST /sgir/v1/m3/inventory/discover-backups-custom/{servidor_id}/{credencial_id}/{ruta_id}?days={days}&deep={deep}")
    result = run_custom_server_integrated_file_discovery(
        db, servidor_id, credencial_id, ruta_id, current_user.id_usuario, days=days, deep=deep
    )
    print(f"[DEBUG discover_custom_backups] Resultado: {result}")
    if isinstance(result, list):
        print(f"[DEBUG discover_custom_backups] Tamaño del array: {len(result)}")
    if isinstance(result, dict) and "error" in result:
        raise HTTPException(status_code=404, detail=result["error"])
    return result


@m3_router.post("/discover-all-backups")
def discover_all_backups(
    db: Session = Depends(get_pg_db),
    current_user: User = Depends(get_current_user)
):
    """
    Inicia un auto-descubrimiento global de respaldos en todos los servidores que tengan
    al menos una ruta de respaldo física asociada.
    """
    from app.services.monitoring.ssh_service import run_bulk_backups_discovery
    return run_bulk_backups_discovery(db, current_user.id_usuario)

@m2_router.get("/summary/{servidor_id}")
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
