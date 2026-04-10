from sqlalchemy.orm import Session
from app.models.audit_model import Bitacora, TipoEventoAuditoria
from app.schemas.audit_schemas import BitacoraCreate, TipoEventoCreate

def log_event(
    db: Session, 
    user_id: int, 
    entidad: str, 
    entidad_id: int, 
    descripcion: str, 
    tipo_evento_id: int
) -> Bitacora:
    """
    Registra un evento en la Bitácora de auditoría.
    IDs Sugeridos (según seed): 1: Creación, 2: Modificación, 3: Eliminación, 4: Ejecución, 5: Alarma
    """
    db_event: Bitacora = Bitacora(
        entidad_afectada=entidad,
        id_entidad=entidad_id,
        descripcion_evento=descripcion,
        id_usuario=user_id,
        id_tipo_evento=tipo_evento_id
    )
    db.add(db_event)
    db.commit()
    db.refresh(db_event)
    return db_event

# Funciones adicionales para Bitácora
def get_bitacoras(db: Session, skip: int = 0, limit: int = 100):
    return db.query(Bitacora).offset(skip).limit(limit).all()

def get_bitacora_by_id(db: Session, bitacora_id: int):
    return db.query(Bitacora).filter(Bitacora.id_bitacora == bitacora_id).first()

# CRUD para TipoEventoAuditoria
def get_tipo_eventos(db: Session, skip: int = 0, limit: int = 100):
    return db.query(TipoEventoAuditoria).offset(skip).limit(limit).all()

def get_tipo_evento_by_id(db: Session, id_tipo_evento: int):
    return db.query(TipoEventoAuditoria).filter(TipoEventoAuditoria.id_tipo_evento == id_tipo_evento).first()

def create_tipo_evento(db: Session, tipo_evento: TipoEventoCreate):
    db_tipo = TipoEventoAuditoria(nombre_evento=tipo_evento.nombre_evento)
    db.add(db_tipo)
    db.commit()
    db.refresh(db_tipo)
    return db_tipo

def delete_tipo_evento(db: Session, id_tipo_evento: int):
    db_tipo = get_tipo_evento_by_id(db, id_tipo_evento)
    if db_tipo:
        db.delete(db_tipo)
        db.commit()
        return True
    return False
