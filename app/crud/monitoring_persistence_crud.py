from sqlalchemy.orm import Session
from app.models.monitoring_persistence_models import Monitoreo, Metrica, Alerta
from app.schemas.monitoring_persistence_schemas import MonitoreoCreate, MetricaCreate, AlertaCreate
from datetime import datetime

# --- CRUD Monitoreo (Sesiones) ---

from datetime import datetime, timedelta, timezone
from sqlalchemy import delete
from app.models.monitoring_persistence import Metrica, Monitoreo

def purge_old_metrics(db: Session, days: int) -> int:
    """
    Elimina métricas más antiguas que N días.
    Retorna la cantidad de registros eliminados.
    """
    threshold_date = datetime.now(timezone.utc) - timedelta(days=days)

    # Ejecutar el borrado masivo
    stmt = delete(Metrica).where(Metrica.fecha_registro < threshold_date)
    result = db.execute(stmt)
    db.commit()

    return result.rowcount

def create_monitoreo_session(db: Session, session: MonitoreoCreate) -> Monitoreo:

    db_monitoreo: Monitoreo = Monitoreo(**monitoreo.model_dump())
    db.add(db_monitoreo)
    db.commit()
    db.refresh(db_monitoreo)
    return db_monitoreo

def close_monitoreo_session(db: Session, monitoreo_id: int) -> Monitoreo | None:
    db_monitoreo: Monitoreo | None = db.query(Monitoreo).filter(Monitoreo.id_monitoreo == monitoreo_id).first()
    if db_monitoreo:
        db_monitoreo.fecha_fin = datetime.now()
        db.commit()
        db.refresh(db_monitoreo)
    return db_monitoreo

# --- CRUD Métricas (Puntos de datos) ---

def save_metric(db: Session, metrica: MetricaCreate) -> Metrica:
    db_metrica: Metrica = Metrica(**metrica.model_dump())
    db.add(db_metrica)
    db.commit()
    db.refresh(db_metrica)
    return db_metrica

# --- CRUD Alertas ---

def create_alert(db: Session, alerta: AlertaCreate) -> Alerta:
    db_alerta: Alerta = Alerta(**alerta.model_dump())
    db.add(db_alerta)
    db.commit()
    db.refresh(db_alerta)
    return db_alerta

def get_alerts_by_server(db: Session, servidor_id: int) -> list[Alerta]:
    return db.query(Alerta).filter(Alerta.id_servidor == servidor_id).all()
