from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from sqlalchemy.orm import Session
from typing import List
from app.db.postgres.postgres_connection import get_db as get_pg_db
from app.schemas import AsignacionPoliticaBDCreate
from app.services import backup_crud, audit_crud
from app.services.infrastructure.import_service import process_asignaciones_politica_csv
from app.core.dependencies import get_current_user
from app.models.user_models import User

router = APIRouter(dependencies=[Depends(get_current_user)])

@router.post("/import-bulk")
async def import_asignaciones_bulk(
    file: UploadFile = File(...),
    db: Session = Depends(get_pg_db),
    current_user: User = Depends(get_current_user)
):
    """
    Carga masiva de asignaciones de políticas a bases de datos mediante CSV.
    """
    if not file.filename.endswith('.csv'):
        raise HTTPException(status_code=400, detail="El archivo debe ser un CSV")
    
    contents = await file.read()
    try:
        summary = process_asignaciones_politica_csv(db, contents, current_user.id_usuario)
        return summary
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

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
