from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from app.core.security_core import decrypt_password
from app.models.infrastructure import InstanciaDBMS, CredencialAcceso, DBMS, Servidor
from fastapi import HTTPException
from typing import Dict, Any

# Caché global para reutilizar Engines
_engine_cache: Dict[int, Any] = {}

def get_dynamic_engine(db_session: Session, instance_id: int):
    """
    Crea un motor de SQLAlchemy basado en la configuración de la CMDB.
    """
    if instance_id in _engine_cache:
        return _engine_cache[instance_id]

    instance = db_session.query(InstanciaDBMS).filter(InstanciaDBMS.id_instancia == instance_id).first()
    if not instance:
        raise HTTPException(status_code=404, detail="Instancia no encontrada en la CMDB")

    dbms = db_session.query(DBMS).filter(DBMS.id_dbms == instance.id_dbms).first()
    server = db_session.query(Servidor).filter(Servidor.id_servidor == instance.id_servidor).first()
    
    # Buscamos la credencial asociada al servidor
    cred = db_session.query(CredencialAcceso).filter(
        CredencialAcceso.id_servidor == server.id_servidor
    ).first()

    if not cred:
        raise HTTPException(status_code=400, detail="Credenciales no encontradas para el servidor")

    try:
        password = decrypt_password(cred.password_hash)
    except Exception:
        raise HTTPException(status_code=500, detail="Error al desencriptar la contraseña de la base de datos")

    dbms_name = dbms.nombre_dbms.lower()
    
    # Construcción dinámica de URL según el motor detectado en la BD
    if "mysql" in dbms_name:
        url = f"mysql+pymysql://{cred.usuario}:{password}@{server.direccion_ip}:{instance.puerto}/"
    elif "oracle" in db_name := dbms_name:
        # Oracle requiere el nombre de la instancia (SID/Service Name)
        url = f"oracle+oracledb://{cred.usuario}:{password}@{server.direccion_ip}:{instance.puerto}/{instance.nombre_instancia}"
    elif "postgres" in dbms_name:
        url = f"postgresql://{cred.usuario}:{password}@{server.direccion_ip}:{instance.puerto}/{instance.nombre_instancia}"
    else:
        raise HTTPException(status_code=400, detail=f"Soporte dinámico no implementado para {dbms.nombre_dbms}")

    try:
        engine = create_engine(
            url, 
            pool_pre_ping=True, 
            pool_recycle=3600,
            connect_args={"connect_timeout": 5}
        )
        _engine_cache[instance_id] = engine
        return engine
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Fallo al conectar con {server.direccion_ip}: {str(e)}")

def get_dynamic_session(db_session: Session, instance_id: int):
    """
    Genera una sesión temporal para realizar operaciones de monitoreo.
    """
    engine = get_dynamic_engine(db_session, instance_id)
    local_session = sessionmaker(bind=engine)
    session = local_session()
    try:
        return session
    except Exception as e:
        session.close()
        raise e

