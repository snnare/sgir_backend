from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import text
from app.db.postgres.postgres_connection import get_db as get_pg_db
from pydantic import BaseModel
from icmplib import ping

router = APIRouter(prefix="/health", tags=["Health Checks"])

class PingRequest(BaseModel):
    ip: str

@router.get("/postgres")
def health_postgres(db: Session = Depends(get_pg_db)):
    try:
        result = db.execute(text("SELECT 1 + 1 AS sum")).fetchone()
        return {"status": "ok", "db": "PostgreSQL", "result": result[0]}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"PostgreSQL failed: {str(e)}")

@router.post("/ping")
def ping_host(request: PingRequest):
    """Realiza un ping a una IP usando icmplib y devuelve true si es alcanzable, false si no."""
    try:
        # En entornos Docker/Linux sin privilegios root, esto puede fallar a menos que
        # se use privileged=true o se añada cap_add: [NET_RAW]
        host = ping(request.ip, count=1, interval=1, timeout=2)
        return host.is_alive
    except Exception as e:
        # Si falla por falta de permisos de socket, devolvemos false o registramos el error
        print(f"Error ejecutando ping: {str(e)}")
        return False

