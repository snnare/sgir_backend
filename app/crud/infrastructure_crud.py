from typing import Any
from sqlalchemy.orm import Session
from app.models.infrastructure_models import Servidor, CredencialAcceso, InstanciaDBMS, BaseDeDatos, NivelCriticidad, TipoAcceso, DBMS
from app.schemas.infrastructure_schemas  import (
    ServidorCreate, ServidorUpdate, 
    CredencialCreate, CredencialUpdate,
    InstanciaCreate, BaseDatosCreate,
    NivelCriticidadCreate, TipoAccesoCreate, DBMSCreate
)
from app.core.security_core import encrypt_password

# --- CRUD Nivel Criticidad ---

def create_nivel_criticidad(db: Session, nivel: NivelCriticidadCreate) -> NivelCriticidad:
    db_nivel = NivelCriticidad(**nivel.model_dump())
    db.add(db_nivel)
    db.commit()
    db.refresh(db_nivel)
    return db_nivel

def get_niveles_criticidad(db: Session, skip: int = 0, limit: int = 100) -> list[NivelCriticidad]:
    return db.query(NivelCriticidad).offset(skip).limit(limit).all()

def delete_nivel_criticidad(db: Session, id_nivel: int) -> bool:
    db_nivel = db.query(NivelCriticidad).filter(NivelCriticidad.id_nivel_criticidad == id_nivel).first()
    if db_nivel:
        db.delete(db_nivel)
        db.commit()
        return True
    return False

# --- CRUD Tipo Acceso ---

def create_tipo_acceso(db: Session, tipo: TipoAccesoCreate) -> TipoAcceso:
    db_tipo = TipoAcceso(**tipo.model_dump())
    db.add(db_tipo)
    db.commit()
    db.refresh(db_tipo)
    return db_tipo

def get_tipos_acceso(db: Session, skip: int = 0, limit: int = 100) -> list[TipoAcceso]:
    return db.query(TipoAcceso).offset(skip).limit(limit).all()

def delete_tipo_acceso(db: Session, id_tipo: int) -> bool:
    db_tipo = db.query(TipoAcceso).filter(TipoAcceso.id_tipo_acceso == id_tipo).first()
    if db_tipo:
        db.delete(db_tipo)
        db.commit()
        return True
    return False

# --- CRUD DBMS ---

def create_dbms(db: Session, dbms: DBMSCreate) -> DBMS:
    db_dbms = DBMS(**dbms.model_dump())
    db.add(db_dbms)
    db.commit()
    db.refresh(db_dbms)
    return db_dbms

def get_dbms_all(db: Session, skip: int = 0, limit: int = 100) -> list[DBMS]:
    return db.query(DBMS).offset(skip).limit(limit).all()

# --- CRUD Servidor ---

def get_servidor(db: Session, servidor_id: int) -> Servidor | None:
    return db.query(Servidor).filter(Servidor.id_servidor == servidor_id).first()

def get_servidores(db: Session, skip: int = 0, limit: int = 100) -> list[Servidor]:
    return db.query(Servidor).offset(skip).limit(limit).all()

def create_servidor(db: Session, servidor: ServidorCreate) -> Servidor:
    db_servidor: Servidor = Servidor(**servidor.model_dump())
    db.add(db_servidor)
    db.commit()
    db.refresh(db_servidor)
    return db_servidor

def update_servidor(db: Session, servidor_id: int, servidor_update: ServidorUpdate) -> Servidor | None:
    db_servidor = get_servidor(db, servidor_id)
    if not db_servidor:
        return None
    
    update_data = servidor_update.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_servidor, key, value)
    
    db.commit()
    db.refresh(db_servidor)
    return db_servidor

def delete_servidor(db: Session, servidor_id: int) -> bool:
    db_servidor = get_servidor(db, servidor_id)
    if db_servidor:
        db.delete(db_servidor)
        db.commit()
        return True
    return False

# --- CRUD Credencial ---

def get_credencial(db: Session, id_credencial: int) -> CredencialAcceso | None:
    return db.query(CredencialAcceso).filter(CredencialAcceso.id_credencial == id_credencial).first()

def get_credenciales_by_servidor(db: Session, servidor_id: int) -> list[CredencialAcceso]:
    return db.query(CredencialAcceso).filter(CredencialAcceso.id_servidor == servidor_id).all()

def create_credencial(db: Session, credencial: CredencialCreate) -> CredencialAcceso:
    encrypted_pass: str = encrypt_password(credencial.password)
    data: dict[str, Any] = credencial.model_dump(exclude={"password"})
    db_credencial: CredencialAcceso = CredencialAcceso(**data, password_hash=encrypted_pass)
    db.add(db_credencial)
    db.commit()
    db.refresh(db_credencial)
    return db_credencial

def update_credencial(db: Session, id_credencial: int, credencial_update: CredencialUpdate) -> CredencialAcceso | None:
    db_credencial = get_credencial(db, id_credencial)
    if not db_credencial:
        return None
    
    update_data = credencial_update.model_dump(exclude_unset=True)
    if "password" in update_data:
        update_data["password_hash"] = encrypt_password(update_data.pop("password"))
        
    for key, value in update_data.items():
        setattr(db_credencial, key, value)
        
    db.commit()
    db.refresh(db_credencial)
    return db_credencial

def delete_credencial(db: Session, id_credencial: int) -> bool:
    db_credencial = get_credencial(db, id_credencial)
    if db_credencial:
        db.delete(db_credencial)
        db.commit()
        return True
    return False
