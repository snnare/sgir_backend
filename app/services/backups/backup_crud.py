from sqlalchemy.orm import Session
from typing import List, Optional
from app.models.backup_models import (
    RutaRespaldo, PoliticaRespaldo, AsignacionPoliticaBD, Respaldo,
    TipoRespaldo, TipoAlmacenamiento
)
from app.schemas import (
    RutaRespaldoCreate, RutaRespaldoUpdate,
    PoliticaRespaldoCreate, PoliticaRespaldoUpdate,
    RespaldoCreate, AsignacionPoliticaBDCreate,
    TipoRespaldoCreate, TipoAlmacenamientoCreate
)

# --- Catálogos ---

def create_tipo_respaldo(db: Session, tipo: TipoRespaldoCreate) -> TipoRespaldo:
    db_tipo = TipoRespaldo(**tipo.model_dump())
    db.add(db_tipo)
    db.commit()
    db.refresh(db_tipo)
    return db_tipo

def get_tipos_respaldo(db: Session) -> List[TipoRespaldo]:
    return db.query(TipoRespaldo).all()

def delete_tipo_respaldo(db: Session, id_tipo: int) -> bool:
    db_tipo = db.query(TipoRespaldo).filter(TipoRespaldo.id_tipo_respaldo == id_tipo).first()
    if db_tipo:
        db.delete(db_tipo)
        db.commit()
        return True
    return False

def create_tipo_almacenamiento(db: Session, tipo: TipoAlmacenamientoCreate) -> TipoAlmacenamiento:
    db_tipo = TipoAlmacenamiento(**tipo.model_dump())
    db.add(db_tipo)
    db.commit()
    db.refresh(db_tipo)
    return db_tipo

def get_tipos_almacenamiento(db: Session) -> List[TipoAlmacenamiento]:
    return db.query(TipoAlmacenamiento).all()

def delete_tipo_almacenamiento(db: Session, id_tipo: int) -> bool:
    db_tipo = db.query(TipoAlmacenamiento).filter(TipoAlmacenamiento.id_tipo_almacenamiento == id_tipo).first()
    if db_tipo:
        db.delete(db_tipo)
        db.commit()
        return True
    return False

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

def update_ruta_respaldo(db: Session, id_ruta: int, ruta_update: RutaRespaldoUpdate) -> Optional[RutaRespaldo]:
    db_ruta = get_ruta_respaldo(db, id_ruta)
    if not db_ruta:
        return None
    for key, value in ruta_update.model_dump(exclude_unset=True).items():
        setattr(db_ruta, key, value)
    db.commit()
    db.refresh(db_ruta)
    return db_ruta

def delete_ruta_respaldo(db: Session, id_ruta: int) -> bool:
    db_ruta = get_ruta_respaldo(db, id_ruta)
    if db_ruta:
        db.delete(db_ruta)
        db.commit()
        return True
    return False

# --- Políticas de Respaldo ---

def create_politica_respaldo(db: Session, politica: PoliticaRespaldoCreate) -> PoliticaRespaldo:
    db_politica = PoliticaRespaldo(**politica.model_dump())
    db.add(db_politica)
    db.commit()
    db.refresh(db_politica)
    return db_politica

def get_politicas_respaldo(db: Session) -> List[PoliticaRespaldo]:
    return db.query(PoliticaRespaldo).all()

def get_politica_respaldo(db: Session, id_politica: int) -> Optional[PoliticaRespaldo]:
    return db.query(PoliticaRespaldo).filter(PoliticaRespaldo.id_politica == id_politica).first()

def update_politica_respaldo(db: Session, id_politica: int, politica_update: PoliticaRespaldoUpdate) -> Optional[PoliticaRespaldo]:
    db_politica = get_politica_respaldo(db, id_politica)
    if not db_politica:
        return None
    for key, value in politica_update.model_dump(exclude_unset=True).items():
        setattr(db_politica, key, value)
    db.commit()
    db.refresh(db_politica)
    return db_politica

def delete_politica_respaldo(db: Session, id_politica: int) -> bool:
    db_politica = get_politica_respaldo(db, id_politica)
    if db_politica:
        db.delete(db_politica)
        db.commit()
        return True
    return False

# --- Asignaciones ---

def asignar_politica_a_bd(db: Session, asignacion: AsignacionPoliticaBDCreate) -> AsignacionPoliticaBD:
    db_asignacion = AsignacionPoliticaBD(**asignacion.model_dump())
    db.add(db_asignacion)
    db.commit()
    db.refresh(db_asignacion)
    return db_asignacion

def eliminar_asignacion_politica(db: Session, id_base_datos: int, id_politica: int) -> bool:
    db_asignacion = db.query(AsignacionPoliticaBD).filter(
        AsignacionPoliticaBD.id_base_datos == id_base_datos,
        AsignacionPoliticaBD.id_politica == id_politica
    ).first()
    if db_asignacion:
        db.delete(db_asignacion)
        db.commit()
        return True
    return False

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
