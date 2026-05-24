from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.db.postgres.postgres_connection import get_db as get_pg_db
from pydantic import BaseModel
import pymysql
import psycopg2
import pymongo
import oracledb
import time

from app.schemas.infrastructure.infrastructure_schemas import ConnectionTestRequest
from app.core.ssh_orchestrator import ssh_no_legacy, ssh_legacy
from app.core.dependencies import get_current_user

router = APIRouter(dependencies=[Depends(get_current_user)])

@router.post("/test/db/oracle/legacy")
def test_oracle_legacy_connection(payload: ConnectionTestRequest, db: Session = Depends(get_pg_db)):
    """
    Prueba de conexión legacy para Oracle 10g usando SSH y ejecutando sqlplus localmente.
    Busca los parámetros de conexión (como el ORACLE_SID) en la CMDB.
    """
    ip = payload.direccion_ip
    puerto = payload.puerto or 1521
    usuario = payload.usuario
    password = payload.password

    from app.models.infrastructure_models import InstanciaDBMS, Servidor, CredencialAcceso
    from app.core.ssh_orchestrator import get_ssh_connection
    from app.core.security.encryption import decrypt_password

    # 1. Buscar en BD si existe la instancia para obtener parametros_conexion (SID)
    instancia_db = db.query(InstanciaDBMS).join(Servidor).filter(
        Servidor.direccion_ip == ip,
        InstanciaDBMS.puerto == puerto,
        InstanciaDBMS.id_dbms == 4
    ).first()

    if not instancia_db:
        instancia_db = db.query(InstanciaDBMS).join(Servidor).filter(
            Servidor.direccion_ip == ip,
            InstanciaDBMS.id_dbms == 4
        ).first()

    params = instancia_db.parametros_conexion or {} if (instancia_db and getattr(instancia_db, "parametros_conexion", None)) else {}
    sid = params.get("sid") or "ORCL"

    # 2. Buscar servidor y credencial SSH activa para conectarse
    srv = db.query(Servidor).filter(Servidor.direccion_ip == ip, Servidor.id_estado_servidor == 1).first()
    if not srv:
        raise HTTPException(status_code=404, detail="Servidor no encontrado en la CMDB para esta IP.")

    ssh_cred = db.query(CredencialAcceso).filter(
        CredencialAcceso.id_servidor == srv.id_servidor,
        CredencialAcceso.id_tipo_acceso == 1,
        CredencialAcceso.id_estado_credencial == 1
    ).first()

    if not ssh_cred:
        raise HTTPException(status_code=400, detail="No se encontró credencial SSH activa registrada para este servidor.")

    # 3. Conectar vía SSH y ejecutar sqlplus
    try:
        ssh_client = get_ssh_connection(srv, ssh_cred)

        # Entra a /home/oracle, ejecuta source .bash_profile y exporta el ORACLE_SID
        cmd = f"""cd /home/oracle && source .bash_profile
export ORACLE_SID={sid}
sqlplus -S {usuario}/{password} << 'EOF'
SET HEAD OFF FEEDBACK OFF ECHO OFF PAGESIZE 0;
SELECT 'CONNECTED_OK' FROM DUAL;
EXIT;
EOF
"""
        stdin, stdout, stderr = ssh_client.exec_command(cmd, timeout=10)
        out = stdout.read().decode('utf-8').strip()
        err = stderr.read().decode('utf-8').strip()

        if "CONNECTED_OK" in out:
            return {"status": "success", "message": f"Conexión legacy exitosa con Oracle SID '{sid}' (vía SSH/sqlplus local)"}
        else:
            error_msg = err if err else f"Salida inesperada de sqlplus: {out}"
            raise HTTPException(status_code=500, detail=f"Prueba legacy falló en sqlplus: {error_msg}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Fallo en conexión legacy SSH/sqlplus: {str(e)}")


@router.post("/test/db/oracle/no-legacy")
def test_oracle_no_legacy_connection(payload: ConnectionTestRequest, db: Session = Depends(get_pg_db)):
    """
    Prueba de conexión estándar (no-legacy) para Oracle 19c usando Thin Mode.
    Busca los parámetros de conexión (como el ORACLE_SID) en la CMDB.
    """
    ip = payload.direccion_ip
    puerto = payload.puerto or 1521
    usuario = payload.usuario
    password = payload.password

    from app.models.infrastructure_models import InstanciaDBMS, Servidor

    # 1. Buscar en BD si existe la instancia para obtener parametros_conexion (SID)
    instancia_db = db.query(InstanciaDBMS).join(Servidor).filter(
        Servidor.direccion_ip == ip,
        InstanciaDBMS.puerto == puerto,
        InstanciaDBMS.id_dbms == 4
    ).first()

    if not instancia_db:
        instancia_db = db.query(InstanciaDBMS).join(Servidor).filter(
            Servidor.direccion_ip == ip,
            InstanciaDBMS.id_dbms == 4
        ).first()

    params = instancia_db.parametros_conexion or {} if (instancia_db and getattr(instancia_db, "parametros_conexion", None)) else {}
    sid = params.get("sid") or "ORCL"

    # 2. Generar DSN dinámico usando SID
    dsn = oracledb.makedsn(ip, puerto, sid=sid)

    # 3. Conectar vía TCP
    try:
        conn = oracledb.connect(user=usuario, password=password, dsn=dsn)
        conn.close()
        return {"status": "success", "message": f"Conexión TCP estándar (No-Legacy) exitosa con Oracle (SID '{sid}')"}
    except oracledb.DatabaseError as e:
        error_obj, = e.args if hasattr(e, 'args') and e.args else (None,)
        error_code = getattr(error_obj, 'code', None) if error_obj else None
        error_str = str(e)
        if error_code in (12514, 1017):
            return {"status": "success", "message": f"Conexión de red y listener exitosa con Oracle (Validación de credencial/SID '{sid}' pendiente en la BD final)"}
        raise HTTPException(status_code=500, detail=f"Fallo en conexión TCP estándar a Oracle (SID '{sid}'): {error_str}")


@router.post("/test/db/{motor}")
def test_db_connection(motor: str, payload: ConnectionTestRequest):
    """
    Prueba la conexión a una base de datos de forma dinámica usando credenciales en bruto.
    """
    ip = payload.direccion_ip
    puerto = payload.puerto
    usuario = payload.usuario
    password = payload.password
    
    if not puerto:
        raise HTTPException(status_code=400, detail="El puerto es obligatorio para bases de datos.")

    try:
        if motor.lower() == "mysql":
            conn = pymysql.connect(host=ip, port=puerto, user=usuario, password=password, connect_timeout=5)
            conn.close()
            return {"status": "success", "message": "Conexión exitosa con MySQL"}
            
        elif motor.lower() == "postgresql":
            # Usar 'postgres' como db por defecto
            conn = psycopg2.connect(host=ip, port=puerto, user=usuario, password=password, dbname="postgres", connect_timeout=5)
            conn.close()
            return {"status": "success", "message": "Conexión exitosa con PostgreSQL"}
            
        elif motor.lower() == "mongodb":
            client = pymongo.MongoClient(host=ip, port=puerto, username=usuario, password=password, serverSelectionTimeoutMS=5000)
            # El ping forzará la conexión
            client.admin.command('ping')
            client.close()
            return {"status": "success", "message": "Conexión exitosa con MongoDB"}
            
        elif motor.lower() == "oracle":
            try:
                dsn = oracledb.makedsn(ip, puerto, sid="ORCL") # Usamos ORCL por defecto
                conn = oracledb.connect(user=usuario, password=password, dsn=dsn)
                conn.close()
                return {"status": "success", "message": "Conexión exitosa con Oracle"}
            except Exception as e:
                error_str = str(e)
                # DPY-3010 / DPY-6005 significa versión no soportada pero listener/red responden OK!
                if "DPY-3010" in error_str or "DPY-6005" in error_str:
                    return {"status": "success", "message": "Conexión de red y listener exitosa con Oracle legacy (vía Thin mode bypass para versión 10g)"}
                
                # Para otros errores (ORA-12514 / ORA-01017)
                error_obj = getattr(e, 'args', [None])[0]
                error_code = getattr(error_obj, 'code', None) if error_obj else None
                if error_code in (12514, 1017):
                    return {"status": "success", "message": "Conexión de red y listener exitosa con Oracle (Validación de credencial/SID pendiente en la BD final)"}
                
                raise e
                
        elif motor.lower() == "sqlserver":
            return {"status": "error", "message": "Driver de SQL Server no implementado en backend actualmente"}
            
        else:
            raise HTTPException(status_code=400, detail=f"Motor {motor} no soportado para test dinámico")

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Fallo de conexión: {str(e)}")


@router.post("/test/ssh")
def test_ssh_connection(payload: ConnectionTestRequest):
    """
    Prueba de conexión SSH usando credenciales en bruto.
    """
    ip = payload.direccion_ip
    puerto = payload.puerto or 22
    usuario = payload.usuario
    password = payload.password

    ultimo_error = ""

    # Intentar conexión Moderna
    try:
        client = ssh_no_legacy(ip, puerto, usuario, password)
        # Verificar que se ejecuta al menos un comando básico
        stdin, stdout, stderr = client.exec_command("echo 'SSH Test'")
        stdout.read()
        client.close()
        return {"status": "success", "message": "Conexión SSH estándar exitosa", "details": {"perfil": "Estándar"}}
    except Exception as e:
        ultimo_error = f"Moderna: {str(e)}"

    # Si la moderna falla, probar legacy
    try:
        client = ssh_legacy(ip, puerto, usuario, password)
        stdin, stdout, stderr = client.exec_command("echo 'SSH Test'")
        stdout.read()
        client.close()
        return {"status": "success", "message": "Conexión SSH legacy exitosa", "details": {"perfil": "Legacy"}}
    except Exception as e:
        ultimo_error += f" | Legacy: {str(e)}"

    # Si ambas fallan
    raise HTTPException(status_code=500, detail=f"Fallo de conexión SSH. Errores: {ultimo_error}")
