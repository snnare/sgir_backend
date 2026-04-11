from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from app.models.infrastructure_models import Servidor, CredencialAcceso
from app.core.security.encryption import decrypt_password
from fastapi import HTTPException

def get_dynamic_engine(servidor: Servidor, credencial: CredencialAcceso, db_name: str = None):
    """
    Genera un engine de SQLAlchemy dinámicamente basado en el tipo de DBMS y credenciales.
    """
    password = decrypt_password(credencial.password_hash)
    host = servidor.direccion_ip
    user = credencial.usuario
    
    # Determinar el puerto y el driver según el DBMS (asumiendo IDs de la seed)
    # 1: Postgres, 2: MySQL 5, 3: MySQL 8, 4: Oracle, 5: Mongo
    dbms_id = 2 # Por ahora hardcoded para MySQL 5 como solicitaste
    
    if dbms_id in [2, 3]: # MySQL
        # Intentar conectar al puerto 3305 si el host es localhost (para Docker) o 3306 por defecto
        port = 3305 if host in ["localhost", "127.0.0.1"] else 3306
        driver = "mysql+pymysql"
        url = f"{driver}://{user}:{password}@{host}:{port}/{db_name if db_name else ''}"
    else:
        raise HTTPException(status_code=400, detail="DBMS no soportado para conexión dinámica actualmente")

    return create_engine(url, connect_args={"connect_timeout": 5})

def get_dynamic_session(servidor: Servidor, credencial: CredencialAcceso, db_name: str = None) -> Session:
    """Crea una sesión temporal para el servidor remoto."""
    engine = get_dynamic_engine(servidor, credencial, db_name)
    SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)
    return SessionLocal()
