from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import text
from app.db.mysql.mysql5 import get_mysql5_db
from app.schemas.monitoring.mysql5 import (
    MySQL5Connection, 
    MySQL5FullMetrics, 
    MySQL5Availability, 
    MySQL5Saturation, 
    MySQL5Performance, 
    MySQL5Capacity
)
from app.crud.monitoring.mysql.mysql5 import get_mysql5_metrics
from typing import List
from app.core.dependencies import get_current_user

router = APIRouter(
    prefix="/mysql5", 
    tags=["Monitoring - MySQL 5"],
    dependencies=[Depends(get_current_user)]
)

@router.get("/metrics", response_model=MySQL5FullMetrics)
def get_full_metrics(db: Session = Depends(get_mysql5_db)):
    try:
        return get_mysql5_metrics(db)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/metrics/availability", response_model=MySQL5Availability)
def get_availability(db: Session = Depends(get_mysql5_db)):
    try:
        metrics = get_mysql5_metrics(db)
        return metrics["availability"]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/metrics/saturation", response_model=MySQL5Saturation)
def get_saturation(db: Session = Depends(get_mysql5_db)):
    try:
        metrics = get_mysql5_metrics(db)
        return metrics["saturation"]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/metrics/performance", response_model=MySQL5Performance)
def get_performance(db: Session = Depends(get_mysql5_db)):
    try:
        metrics = get_mysql5_metrics(db)
        return metrics["performance"]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/metrics/capacity", response_model=MySQL5Capacity)
def get_capacity(db: Session = Depends(get_mysql5_db)):
    try:
        metrics = get_mysql5_metrics(db)
        return metrics["capacity"]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/connections", response_model=List[MySQL5Connection])
def get_mysql5_connections(db: Session = Depends(get_mysql5_db)):
    try:
        query = text("SHOW FULL PROCESSLIST")
        result = db.execute(query).fetchall()
        
        connections = []
        for row in result:
            connections.append(
                MySQL5Connection(
                    id=row[0],
                    user=row[1],
                    host=row[2],
                    db=row[3],
                    command=row[4],
                    time=row[5],
                    state=row[6],
                    info=row[7]
                )
            )
        return connections
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
