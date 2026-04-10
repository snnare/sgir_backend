from typing import Any
from sqlalchemy.orm import Session
from app.models.infrastructure_models import Servidor, CredencialAcceso, InstanciaDBMS, BaseDeDatos
from app.schemas.infrastructure_schemas  import ServidorCreate, CredencialCreate, InstanciaCreate, BaseDatosCreate
from app.core.security_core import encrypt_password

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

# --- CRUD Credencial ---

def create_credencial(db: Session, credencial: CredencialCreate) -> CredencialAcceso:
    # Encriptar la contraseña (AES reversible) en lugar de hashear (Bcrypt)
    # Esto permite que el sistema use la contraseña para conectarse vía SSH/DB.
    encrypted_pass: str = encrypt_password(credencial.password)
    data: dict[str, Any] = credencial.model_dump(exclude={"password"})
    db_credencial: CredencialAcceso = CredencialAcceso(**data, password_hash=encrypted_pass)
    db.add(db_credencial)
    db.commit()
    db.refresh(db_credencial)
    return db_credencial

# --- CRUD Instancia ---

def get_instancias_by_servidor(db: Session, servidor_id: int) -> list[InstanciaDBMS]:
    return db.query(InstanciaDBMS).filter(InstanciaDBMS.id_servidor == servidor_id).all()

def create_instancia(db: Session, instancia: InstanciaCreate) -> InstanciaDBMS:
    db_instancia: InstanciaDBMS = InstanciaDBMS(**instancia.model_dump())
    db.add(db_instancia)
    db.commit()
    db.refresh(db_instancia)
    return db_instancia

# --- CRUD Base de Datos ---

def create_base_datos(db: Session, base_datos: BaseDatosCreate) -> BaseDeDatos:
    db_bd: BaseDeDatos = BaseDeDatos(**base_datos.model_dump())
    db.add(db_bd)
    db.commit()
    db.refresh(db_bd)
    return db_bd
