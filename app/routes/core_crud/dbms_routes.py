from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from app.db.postgres.postgres_connection import get_db as get_pg_db
from app.schemas.infrastructure_schemas import DBMSCreate, DBMSResponse
from app.crud import infrastructure_crud
from app.core.dependencies import get_current_user

router = APIRouter(dependencies=[Depends(get_current_user)])

@router.post("/", response_model=DBMSResponse, status_code=status.HTTP_201_CREATED)
def create_dbms(dbms: DBMSCreate, db: Session = Depends(get_pg_db)):
    return infrastructure_crud.create_dbms(db, dbms)

@router.get("/", response_model=List[DBMSResponse])
def read_dbms_all(skip: int = 0, limit: int = 100, db: Session = Depends(get_pg_db)):
    return infrastructure_crud.get_dbms_all(db, skip, limit)
