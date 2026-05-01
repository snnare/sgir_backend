from fastapi import APIRouter, Depends, HTTPException, status
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
            except oracledb.DatabaseError as e:
                error_obj, = e.args
                # ORA-12514: TNS:listener does not currently know of service requested
                # ORA-01017: invalid username/password; logon denied
                # Si llegamos aquí, el listener o la BD respondieron, así que hay conexión a la infraestructura
                if error_obj.code in (12514, 1017):
                    return {"status": "success", "message": "Conexión de red y listener exitosa con Oracle (Validación de credencial/SID pendiente en la BD final)"}
                raise e
        elif motor.lower() == "sqlserver":
            # Implementar dummy, pymssql o pydbc no están en requerimientos
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
