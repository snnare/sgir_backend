from app.models.infrastructure_models import Servidor, CredencialAcceso
from app.core.security.encryption import decrypt_password
from app.core.db_pool_manager import db_pool
from fastapi import HTTPException

import urllib.parse

def get_dynamic_url(servidor: Servidor, credencial: CredencialAcceso, dbms_id: int, db_name: str = None):
    """Genera el string de conexión dinámico."""
    raw_password = decrypt_password(credencial.password_hash)
    password = urllib.parse.quote_plus(raw_password)
    host = servidor.direccion_ip
    user = credencial.usuario
    
    if dbms_id in [2, 3]: # MySQL
        if host in ["localhost", "127.0.0.1"]:
            port = 3305 if dbms_id == 2 else 3308
        else:
            port = 3306
        driver = "mysql+pymysql"
        charset = "utf8" if dbms_id == 2 else "utf8mb4"
        return f"{driver}://{user}:{password}@{host}:{port}/{db_name if db_name else ''}?charset={charset}"
    
    elif dbms_id == 4: # Oracle
        port = 1521
        service_name = db_name if db_name else "XEPDB1" 
        return f"oracle+oracledb://{user}:{password}@{host}:{port}/?service_name={service_name}"

    elif dbms_id == 5: # MongoDB
        port = 27017
        return f"mongodb://{user}:{password}@{host}:{port}/?authSource=admin"
    
    else:
        raise HTTPException(status_code=400, detail="DBMS no soportado para conexión dinámica")

def get_dynamic_session(servidor: Servidor, credencial: CredencialAcceso, dbms_id: int, db_name: str = None):
    """Obtiene una sesión del pool persistente."""
    url = get_dynamic_url(servidor, credencial, dbms_id, db_name)
    pool_key = f"{servidor.direccion_ip}_{dbms_id}_{db_name}"

    if dbms_id == 5: # MongoDB
        return db_pool.get_mongo_client(pool_key, url)
    
    # RDBMS (MySQL, Oracle)
    return db_pool.get_rdbms_session(pool_key, url)

