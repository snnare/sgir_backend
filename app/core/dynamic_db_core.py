from app.models.infrastructure_models import Servidor, CredencialAcceso
from app.core.security.encryption import decrypt_password
from app.core.db_pool_manager import db_pool
from fastapi import HTTPException

import urllib.parse

def get_dynamic_url(servidor: Servidor, credencial: CredencialAcceso, dbms_id: int, db_name: str = None, parametros: dict = None):
    """Genera el string de conexión dinámico."""
    raw_password = decrypt_password(credencial.password_hash)
    password = urllib.parse.quote_plus(raw_password)
    host = servidor.direccion_ip
    user = credencial.usuario
    params = parametros or {}
    
    if dbms_id in [2, 3]: # MySQL
        if host in ["localhost", "127.0.0.1"]:
            port = 3305 if dbms_id == 2 else 3308
        else:
            port = 3306
        port = params.get("port") or params.get("puerto") or port
        driver = "mysql+pymysql"
        charset = params.get("charset") or "utf8mb4"
        url = f"{driver}://{user}:{password}@{host}:{port}/{db_name if db_name else ''}?charset={charset}"
        if "ssl_ca" in params:
            url += f"&ssl_ca={params['ssl_ca']}"
        return url
    
    elif dbms_id == 4: # Oracle
        port = params.get("port") or params.get("puerto") or 1521
        if "sid" in params:
            return f"oracle+oracledb://{user}:{password}@{host}:{port}/?sid={params['sid']}"
        else:
            service_name = params.get("service_name") or db_name or "XEPDB1" 
            return f"oracle+oracledb://{user}:{password}@{host}:{port}/?service_name={service_name}"

    elif dbms_id == 5: # MongoDB
        port = params.get("port") or params.get("puerto") or 27017
        auth_source = params.get("authSource") or "admin"
        return f"mongodb://{user}:{password}@{host}:{port}/?authSource={auth_source}"
    
    else:
        raise HTTPException(status_code=400, detail="DBMS no soportado para conexión dinámica")

def get_dynamic_session(servidor: Servidor, credencial: CredencialAcceso, dbms_id: int, db_name: str = None, parametros: dict = None):
    """Obtiene una sesión del pool persistente."""
    url = get_dynamic_url(servidor, credencial, dbms_id, db_name, parametros)
    
    # Asegurar llaves únicas de pool basadas en parámetros de conexión (ej. diferentes SIDs en misma IP)
    params_str = f"_{str(parametros)}" if parametros else ""
    pool_key = f"{servidor.direccion_ip}_{dbms_id}_{db_name}{params_str}"

    if dbms_id == 5: # MongoDB
        return db_pool.get_mongo_client(pool_key, url)
    
    # RDBMS (MySQL, Oracle)
    return db_pool.get_rdbms_session(pool_key, url)


