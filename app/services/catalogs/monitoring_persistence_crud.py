from sqlalchemy.orm import Session
from app.models.monitoring_persistence_models import Monitoreo, Metrica, Alerta, TipoMetrica, NivelAlerta
from app.schemas import (
    MonitoreoCreate, MetricaCreate, AlertaCreate,
    TipoMetricaCreate, NivelAlertaCreate
)
from datetime import datetime, timedelta, timezone
from sqlalchemy import delete

# --- CRUD Tipo Metrica ---

def create_tipo_metrica(db: Session, tipo: TipoMetricaCreate) -> TipoMetrica:
    db_tipo = TipoMetrica(**tipo.model_dump())
    db.add(db_tipo)
    db.commit()
    db.refresh(db_tipo)
    return db_tipo

def get_tipos_metrica(db: Session) -> list[TipoMetrica]:
    return db.query(TipoMetrica).all()

def delete_tipo_metrica(db: Session, id_tipo: int) -> bool:
    db_tipo = db.query(TipoMetrica).filter(TipoMetrica.id_tipo_metrica == id_tipo).first()
    if db_tipo:
        db.delete(db_tipo)
        db.commit()
        return True
    return False

# --- CRUD Nivel Alerta ---

def create_nivel_alerta(db: Session, nivel: NivelAlertaCreate) -> NivelAlerta:
    db_nivel = NivelAlerta(**nivel.model_dump())
    db.add(db_nivel)
    db.commit()
    db.refresh(db_nivel)
    return db_nivel

def get_niveles_alerta(db: Session) -> list[NivelAlerta]:
    return db.query(NivelAlerta).all()

def delete_nivel_alerta(db: Session, id_nivel: int) -> bool:
    db_nivel = db.query(NivelAlerta).filter(NivelAlerta.id_nivel_alerta == id_nivel).first()
    if db_nivel:
        db.delete(db_nivel)
        db.commit()
        return True
    return False

# --- CRUD Monitoreo (Sesiones) ---

def purge_old_metrics(db: Session, days: int) -> int:
    """
    Elimina métricas más antiguas que N días.
    Retorna la cantidad de registros eliminados.
    """
    threshold_date = datetime.now(timezone.utc) - timedelta(days=days)
    stmt = delete(Metrica).where(Metrica.fecha_registro < threshold_date)
    result = db.execute(stmt)
    db.commit()
    return result.rowcount

def create_monitoreo_session(db: Session, session: MonitoreoCreate) -> Monitoreo:
    db_monitoreo: Monitoreo = Monitoreo(**session.model_dump())
    db.add(db_monitoreo)
    db.commit()
    db.refresh(db_monitoreo)
    return db_monitoreo

def get_monitoreo_session(db: Session, monitoreo_id: int) -> Monitoreo | None:
    return db.query(Monitoreo).filter(Monitoreo.id_monitoreo == monitoreo_id).first()

def close_monitoreo_session(db: Session, monitoreo_id: int) -> Monitoreo | None:
    db_monitoreo = get_monitoreo_session(db, monitoreo_id)
    if db_monitoreo:
        db_monitoreo.fecha_fin = datetime.now(timezone.utc)
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

def get_active_alerts(db: Session) -> list[Alerta]:
    """Obtiene todas las alertas con estado 'Abierta' (ID 6)."""
    return db.query(Alerta).filter(Alerta.id_estado_alerta == 6).order_by(Alerta.fecha_alerta.desc()).all()

def resolve_alert(db: Session, alerta_id: int) -> Alerta | None:
    """Marca una alerta como 'Cerrada' (ID 7)."""
    db_alerta = db.query(Alerta).filter(Alerta.id_alerta == alerta_id).first()
    if db_alerta:
        db_alerta.id_estado_alerta = 7 # Cerrada
        db.commit()
        db.refresh(db_alerta)
    return db_alerta

def get_alerts_summary(db: Session):
    """Retorna un conteo de alertas activas por nivel."""
    from sqlalchemy import func
    return db.query(
        Alerta.id_nivel_alerta, 
        func.count(Alerta.id_alerta)
    ).filter(Alerta.id_estado_alerta == 6).group_by(Alerta.id_nivel_alerta).all()
