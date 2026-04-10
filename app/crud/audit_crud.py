from sqlalchemy.orm import Session
from app.models.audit_model import Bitacora

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
