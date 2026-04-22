from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from app.db.postgres.postgres_connection import get_db as get_pg_db
from app.schemas.infrastructure_schemas import TipoAccesoCreate, TipoAccesoResponse
from app.services import infrastructure_crud
from app.core.dependencies import get_current_user

router = APIRouter(dependencies=[Depends(get_current_user)])

@router.post("/", response_model=TipoAccesoResponse, status_code=status.HTTP_201_CREATED)
def create_tipo(tipo: TipoAccesoCreate, db: Session = Depends(get_pg_db)):
    return infrastructure_crud.create_tipo_acceso(db, tipo)

@router.get("/", response_model=List[TipoAccesoResponse])
def read_tipos(skip: int = 0, limit: int = 100, db: Session = Depends(get_pg_db)):
    return infrastructure_crud.get_tipos_acceso(db, skip, limit)

@router.delete("/{tipo_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_tipo(tipo_id: int, db: Session = Depends(get_pg_db)):
    if not infrastructure_crud.delete_tipo_acceso(db, tipo_id):
        raise HTTPException(status_code=404, detail="Tipo de acceso no encontrado")
    return None
