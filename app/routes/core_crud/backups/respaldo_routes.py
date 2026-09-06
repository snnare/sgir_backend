from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
from app.db.postgres.postgres_connection import get_db as get_pg_db
from app.schemas import RespaldoCreate, RespaldoResponse, BackupHistoryEnrichedResponse, ReplicacionRespaldoRequest
from app.services import backup_crud, audit_crud
from app.core.dependencies import get_current_user
from app.models.user_models import User

router = APIRouter(dependencies=[Depends(get_current_user)])

@router.post("/", response_model=RespaldoResponse, status_code=status.HTTP_201_CREATED)
def registrar_ejecucion_respaldo(respaldo: RespaldoCreate, db: Session = Depends(get_pg_db), current_user: User = Depends(get_current_user)):
    new_respaldo = backup_crud.create_registro_respaldo(db, respaldo)
    audit_crud.log_event(
        db=db,
        user_id=current_user.id_usuario,
        entidad="Respaldo",
        entidad_id=new_respaldo.id_respaldo,
        descripcion=f"Ejecución de respaldo registrada para BD ID: {respaldo.id_base_datos}. Estado: {respaldo.id_estado_ejecucion}",
        tipo_evento_id=5 # Ejecución
    )
    return new_respaldo

@router.get("/historial", response_model=List[RespaldoResponse])
def read_historial_respaldos(id_base_datos: Optional[int] = None, db: Session = Depends(get_pg_db)):
    return backup_crud.get_historial_respaldos(db, id_base_datos)

@router.get("/historial-enriquecido", response_model=List[BackupHistoryEnrichedResponse])
def read_historial_respaldos_enriquecido(id_base_datos: Optional[int] = None, db: Session = Depends(get_pg_db)):
    return backup_crud.get_historial_respaldos_enriquecido(db, id_base_datos)

@router.get("/", response_model=List[RespaldoResponse])
def read_respaldos(id_base_datos: Optional[int] = None, db: Session = Depends(get_pg_db)):
    return backup_crud.get_historial_respaldos(db, id_base_datos)

@router.post("/{respaldo_id}/replicate")
def replicar_respaldo(
    respaldo_id: int,
    payload: ReplicacionRespaldoRequest,
    db: Session = Depends(get_pg_db),
    current_user: User = Depends(get_current_user)
):
    """
    Descarga o replica un respaldo físico.
    Si respaldo_id es 0, realiza una transferencia directa por ruta física sin requerir registro previo en DB.
    Si payload.destino_ruta_id es nulo o se omite, se descarga localmente al almacenamiento central del backend.
    En caso contrario, se realiza una replicación en puente hacia el servidor SFTP de la ruta indicada.
    """
    from app.services.backups import replication_service
    if respaldo_id == 0:
        if not payload.remote_path or not payload.servidor_id or not payload.credencial_id:
            raise HTTPException(
                status_code=400, 
                detail="Faltan parámetros requeridos para descarga directa (remote_path, servidor_id, credencial_id)"
            )
        if payload.destino_ruta_id is None:
            return replication_service.download_raw_to_local(
                db, payload.servidor_id, payload.credencial_id, payload.remote_path, current_user.id_usuario
            )
        else:
            return replication_service.replicate_raw_to_external(
                db, payload.servidor_id, payload.credencial_id, payload.remote_path, payload.destino_ruta_id, current_user.id_usuario
            )
    else:
        if payload.destino_ruta_id is None:
            return replication_service.download_to_local(db, respaldo_id, current_user.id_usuario)
        else:
            return replication_service.replicate_to_external(db, respaldo_id, payload.destino_ruta_id, current_user.id_usuario)



