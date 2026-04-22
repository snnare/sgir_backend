from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from app.db.postgres.postgres_connection import get_db as get_pg_db
from app.schemas.monitoring_persistence_schemas import NivelAlertaCreate, NivelAlertaResponse
from app.services import monitoring_persistence_crud
from app.core.dependencies import get_current_user

router = APIRouter(dependencies=[Depends(get_current_user)])

@router.post("/", response_model=NivelAlertaResponse, status_code=status.HTTP_201_CREATED)
def create_nivel_alerta(nivel: NivelAlertaCreate, db: Session = Depends(get_pg_db)):
    return monitoring_persistence_crud.create_nivel_alerta(db, nivel)

@router.get("/", response_model=List[NivelAlertaResponse])
def read_niveles_alerta(db: Session = Depends(get_pg_db)):
    return monitoring_persistence_crud.get_niveles_alerta(db)

@router.delete("/{nivel_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_nivel_alerta(nivel_id: int, db: Session = Depends(get_pg_db)):
    if not monitoring_persistence_crud.delete_nivel_alerta(db, nivel_id):
        raise HTTPException(status_code=404, detail="Nivel de alerta no encontrado")
    return None
