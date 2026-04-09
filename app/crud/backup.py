from sqlalchemy.orm import Session
from typing import List, Optional
from app.models.backup import (
    RutaRespaldo, PoliticaRespaldo, AsignacionPoliticaBD, Respaldo,
    TipoRespaldo, TipoAlmacenamiento
)
from app.schemas.backup import (
    RutaRespaldoCreate, PoliticaRespaldoCreate, RespaldoCreate,
    AsignacionPoliticaBDCreate
)

# --- Catálogos ---

def get_tipos_respaldo(db: Session) -> List[TipoRespaldo]:
    return db.query(TipoRespaldo).all()

def get_tipos_almacenamiento(db: Session) -> List[TipoAlmacenamiento]:
    return db.query(TipoAlmacenamiento).all()

# --- Rutas de Respaldo ---

def create_ruta_respaldo(db: Session, ruta: RutaRespaldoCreate) -> RutaRespaldo:
    db_ruta = RutaRespaldo(**ruta.model_dump())
    db.add(db_ruta)
    db.commit()
    db.refresh(db_ruta)
    return db_ruta

def get_rutas_respaldo(db: Session) -> List[RutaRespaldo]:
    return db.query(RutaRespaldo).all()

def get_ruta_respaldo(db: Session, id_ruta: int) -> Optional[RutaRespaldo]:
    return db.query(RutaRespaldo).filter(RutaRespaldo.id_ruta == id_ruta).first()

# --- Políticas de Respaldo ---

def create_politica_respaldo(db: Session, politica: PoliticaRespaldoCreate) -> PoliticaRespaldo:
    db_politica = PoliticaRespaldo(**politica.model_dump())
    db.add(db_politica)
    db.commit()
    db.refresh(db_politica)
    return db_politica

def get_politicas_respaldo(db: Session) -> List[PoliticaRespaldo]:
    return db.query(PoliticaRespaldo).all()

# --- Asignaciones ---

def asignar_politica_a_bd(db: Session, asignacion: AsignacionPoliticaBDCreate) -> AsignacionPoliticaBD:
    db_asignacion = AsignacionPoliticaBD(**asignacion.model_dump())
    db.add(db_asignacion)
    db.commit()
    db.refresh(db_asignacion)
    return db_asignacion

# --- Registros de Respaldo (Auditoría) ---

def create_registro_respaldo(db: Session, respaldo: RespaldoCreate) -> Respaldo:
    """
    Registra el resultado de una verificación (Éxito/Fallo).
    """
    db_respaldo = Respaldo(**respaldo.model_dump())
    db.add(db_respaldo)
    db.commit()
    db.refresh(db_respaldo)
    return db_respaldo

def get_historial_respaldos(db: Session, id_base_datos: Optional[int] = None) -> List[Respaldo]:
    query = db.query(Respaldo)
    if id_base_datos:
        query = query.filter(Respaldo.id_base_datos == id_base_datos)
    return query.order_by(Respaldo.fecha_inicio.desc()).all()
