from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import text
from app.db.postgres.connection import get_db as get_pg_db



router = APIRouter(prefix="/health", tags=["Health Checks"])

@router.get("/ping")
def health_ping(
    ip: str = Query(..., description="Dirección IP a la que realizar el ping"),
    interval: int = Query(60, description="Intervalo sugerido de monitoreo en segundos")
):
    """
    Realiza un ping a una IP específica.
    """
    result = ping_host(ip)
    if result["status"] == "error":
        raise HTTPException(status_code=500, detail=result.get("detail", "Error desconocido en ping"))
    
    return {
        **result,
        "interval_seconds": interval
    }

@router.get("/postgres")
def health_postgres(db: Session = Depends(get_pg_db)):
    try:
        result = db.execute(text("SELECT 1 + 1 AS sum")).fetchone()
        return {"status": "ok", "db": "PostgreSQL", "result": result[0]}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"PostgreSQL failed: {str(e)}")

