from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from sqlalchemy.orm import Session
from typing import List
from app.db.postgres.postgres_connection import get_db as get_pg_db
from app.schemas import AsignacionPoliticaBDCreate, AutoAsignarPoliticaRequest, AutoAsignarPoliticaResponse
from app.services import backup_crud, audit_crud
from app.core.dependencies import get_current_user
from app.models.user_models import User

router = APIRouter(dependencies=[Depends(get_current_user)])

@router.post("/", status_code=status.HTTP_201_CREATED)
def asignar_politica(asignacion: AsignacionPoliticaBDCreate, db: Session = Depends(get_pg_db), current_user: User = Depends(get_current_user)):
    backup_crud.asignar_politica_a_bd(db, asignacion)
    audit_crud.log_event(
        db=db,
        user_id=current_user.id_usuario,
        entidad="AsignacionPoliticaBD",
        entidad_id=asignacion.id_base_datos, # Usamos ID BD como referencia
        descripcion=f"Política ID {asignacion.id_politica} asignada a BD ID {asignacion.id_base_datos}",
        tipo_evento_id=2 # Creación
    )
    return {"message": "Política asignada correctamente"}

@router.delete("/{id_base_datos}/{id_politica}", status_code=status.HTTP_204_NO_CONTENT)
def eliminar_asignacion(id_base_datos: int, id_politica: int, db: Session = Depends(get_pg_db), current_user: User = Depends(get_current_user)):
    if not backup_crud.eliminar_asignacion_politica(db, id_base_datos, id_politica):
        raise HTTPException(status_code=404, detail="Asignación no encontrada")
    audit_crud.log_event(
        db=db,
        user_id=current_user.id_usuario,
        entidad="AsignacionPoliticaBD",
        entidad_id=id_base_datos,
        descripcion=f"Asignación de política ID {id_politica} eliminada de BD ID {id_base_datos}",
        tipo_evento_id=4 # Eliminación
    )
    return None

@router.post("/auto-asociar", response_model=AutoAsignarPoliticaResponse, status_code=status.HTTP_200_OK)
def auto_asociar_politica_bds(
    payload: AutoAsignarPoliticaRequest, 
    db: Session = Depends(get_pg_db), 
    current_user: User = Depends(get_current_user)
):
    """
    Asigna de forma masiva una política a varias BDs de un servidor mediante un listado de nombres.
    """
    try:
        return backup_crud.auto_associate_policy_to_databases(db, payload, current_user.id_usuario)
    except HTTPException as e:
        if e.status_code == 400 and isinstance(e.detail, dict) and "missing_databases" in e.detail:
            from fastapi.responses import JSONResponse
            return JSONResponse(
                status_code=400,
                content={
                    "success": False,
                    "detail": e.detail
                }
            )
        raise e

