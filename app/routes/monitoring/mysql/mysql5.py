from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import text
from app.db.postgres.connection import get_db as get_pg_db
from app.core.dynamic_db_core import get_dynamic_session
from app.core.dependencies import get_current_user

router = APIRouter(
    prefix="/mysql5", 
    tags=["Monitoring - MySQL 5"],
    dependencies=[Depends(get_current_user)]
)

@router.get("/metrics/{id_instancia}", response_model=MySQL5FullMetrics)
def get_full_metrics(id_instancia: int, pg_db: Session = Depends(get_pg_db)):
    """
    Obtiene las 4 Golden Signals de una instancia específica de MySQL 5 usando la CMDB.
    """
    # 1. Obtener la sesión dinámica para el servidor MySQL solicitado
    mysql_db = get_dynamic_session(pg_db, id_instancia)
    
    try:
        # 2. Extraer métricas usando la sesión del servidor remoto
        return get_mysql5_metrics(mysql_db)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al monitorear instancia {id_instancia}: {str(e)}")
    finally:
        mysql_db.close()

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

