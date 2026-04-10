from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import text
from app.db.postgres.postgres_connection import get_db as get_pg_db

router = APIRouter(prefix="/health", tags=["Health Checks"])

@router.get("/postgres")
def health_postgres(db: Session = Depends(get_pg_db)):
    try:
        result = db.execute(text("SELECT 1 + 1 AS sum")).fetchone()
        return {"status": "ok", "db": "PostgreSQL", "result": result[0]}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"PostgreSQL failed: {str(e)}")

