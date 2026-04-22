from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from app.db.postgres.postgres_connection import get_db as get_pg_db
from app.schemas.infrastructure_schemas import NivelCriticidadCreate, NivelCriticidadResponse
from app.services import infrastructure_crud
from app.core.dependencies import get_current_user

router = APIRouter(dependencies=[Depends(get_current_user)])

@router.post("/", response_model=NivelCriticidadResponse, status_code=status.HTTP_201_CREATED)
def create_nivel(nivel: NivelCriticidadCreate, db: Session = Depends(get_pg_db)):
    return infrastructure_crud.create_nivel_criticidad(db, nivel)

@router.get("/", response_model=List[NivelCriticidadResponse])
def read_niveles(skip: int = 0, limit: int = 100, db: Session = Depends(get_pg_db)):
    return infrastructure_crud.get_niveles_criticidad(db, skip, limit)

@router.delete("/{nivel_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_nivel(nivel_id: int, db: Session = Depends(get_pg_db)):
    if not infrastructure_crud.delete_nivel_criticidad(db, nivel_id):
        raise HTTPException(status_code=404, detail="Nivel de criticidad no encontrado")
    return None
