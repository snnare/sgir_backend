from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from app.db.postgres.postgres_connection import get_db as get_pg_db
from app.schemas.user_schemas import RoleCreate, RoleResponse
from app.services import user_crud

from app.core.dependencies import get_current_user

router = APIRouter(dependencies=[Depends(get_current_user)])

@router.post("/", response_model=RoleResponse, status_code=status.HTTP_201_CREATED)
def create_role(role: RoleCreate, db: Session = Depends(get_pg_db)):
    return user_crud.create_role(db=db, role=role)

@router.get("/", response_model=List[RoleResponse])
def read_roles(skip: int = 0, limit: int = 100, db: Session = Depends(get_pg_db)):
    return user_crud.get_roles(db, skip=skip, limit=limit)

@router.get("/{role_id}", response_model=RoleResponse)
def read_role(role_id: int, db: Session = Depends(get_pg_db)):
    db_role = user_crud.get_role_by_id(db, role_id=role_id)
    if db_role is None:
        raise HTTPException(status_code=404, detail="Rol no encontrado")
    return db_role

@router.delete("/{role_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_role(role_id: int, db: Session = Depends(get_pg_db)):
    success = user_crud.delete_role(db, role_id=role_id)
    if not success:
        raise HTTPException(status_code=404, detail="Rol no encontrado")
    return None
