from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from app.models.infrastructure_models import Servidor, CredencialAcceso
from app.core.security.encryption import decrypt_password
from fastapi import HTTPException

def get_dynamic_engine(servidor: Servidor, credencial: CredencialAcceso, dbms_id: int, db_name: str = None):
    """
    Genera un engine de SQLAlchemy dinámicamente basado en el tipo de DBMS y credenciales.
    """
    password = decrypt_password(credencial.password_hash)
    host = servidor.direccion_ip
    user = credencial.usuario
    
    # 1: Postgres, 2: MySQL 5, 3: MySQL 8, 4: Oracle, 5: Mongo
    if dbms_id in [2, 3]: # MySQL
        # Mapeo de puertos para Docker local o default
        if host in ["localhost", "127.0.0.1"]:
            port = 3305 if dbms_id == 2 else 3308
        else:
            port = 3306
        driver = "mysql+pymysql"
        url = f"{driver}://{user}:{password}@{host}:{port}/{db_name if db_name else ''}"
        return create_engine(url, connect_args={"connect_timeout": 5})
    
    elif dbms_id == 5: # MongoDB (NoSQL)
        port = 27017
        # Para MongoDB devolveremos el string de conexión ya que no usa SQLAlchemy Engine estándar de la misma forma
        return f"mongodb://{user}:{password}@{host}:{port}/?authSource=admin"
    
    else:
        raise HTTPException(status_code=400, detail="DBMS no soportado para conexión dinámica actualmente")

def get_dynamic_session(servidor: Servidor, credencial: CredencialAcceso, dbms_id: int, db_name: str = None):
    """Crea una sesión o cliente temporal para el servidor remoto."""
    res = get_dynamic_engine(servidor, credencial, dbms_id, db_name)
    
    if dbms_id == 5: # MongoDB
        from pymongo import MongoClient
        return MongoClient(res, serverSelectionTimeoutMS=5000)
    
    # SQLAlchemy para RDBMS
    SessionLocal = sessionmaker(bind=res, autocommit=False, autoflush=False)
    return SessionLocal()
