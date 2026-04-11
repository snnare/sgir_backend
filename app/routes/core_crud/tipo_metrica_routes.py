from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from app.db.postgres.postgres_connection import get_db as get_pg_db
from app.schemas.monitoring_persistence_schemas import TipoMetricaCreate, TipoMetricaResponse
from app.services import monitoring_persistence_crud
from app.core.dependencies import get_current_user

router = APIRouter(dependencies=[Depends(get_current_user)])

@router.post("/", response_model=TipoMetricaResponse, status_code=status.HTTP_201_CREATED)
def create_tipo_metrica(tipo: TipoMetricaCreate, db: Session = Depends(get_pg_db)):
    return monitoring_persistence_crud.create_tipo_metrica(db, tipo)

@router.get("/", response_model=List[TipoMetricaResponse])
def read_tipos_metrica(db: Session = Depends(get_pg_db)):
    return monitoring_persistence_crud.get_tipos_metrica(db)

@router.delete("/{tipo_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_tipo_metrica(tipo_id: int, db: Session = Depends(get_pg_db)):
    if not monitoring_persistence_crud.delete_tipo_metrica(db, tipo_id):
        raise HTTPException(status_code=404, detail="Tipo de métrica no encontrado")
    return None
