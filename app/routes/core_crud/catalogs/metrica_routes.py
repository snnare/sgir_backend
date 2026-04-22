from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from app.db.postgres.postgres_connection import get_db as get_pg_db
from app.schemas.monitoring_persistence_schemas import MetricaCreate, MetricaResponse
from app.services import monitoring_persistence_crud
from app.core.dependencies import get_current_user

router = APIRouter(dependencies=[Depends(get_current_user)])

@router.post("/", response_model=MetricaResponse, status_code=status.HTTP_201_CREATED)
def save_metric(metrica: MetricaCreate, db: Session = Depends(get_pg_db)):
    return monitoring_persistence_crud.save_metric(db, metrica)
