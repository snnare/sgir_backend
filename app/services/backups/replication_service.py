import os
import hashlib
from decimal import Decimal
from datetime import datetime
from sqlalchemy.orm import Session
from fastapi import HTTPException
from app.models.backup_models import Respaldo, RutaRespaldo, TipoAlmacenamiento
from app.models.infrastructure_models import Servidor, CredencialAcceso, BaseDeDatos, InstanciaDBMS
from app.models.audit_model import Bitacora
from app.core.ssh_orchestrator import get_ssh_connection
import logging

logger = logging.getLogger("replication_service")

# Directorio local por defecto (ubicado en /tmp para evitar problemas de permisos de escritura con sgir_user en Docker)
LOCAL_BACKUPS_DIR = "/tmp/storage/backups"



def download_to_local(db: Session, respaldo_id: int, user_id: int) -> dict:
    """
    Descarga un respaldo remoto por SFTP al almacenamiento local del backend.
    """
    respaldo = db.query(Respaldo).filter(Respaldo.id_respaldo == respaldo_id).first()
    if not respaldo:
        raise HTTPException(status_code=404, detail="Respaldo no encontrado")
        
    # Obtener el servidor de origen y sus credenciales
    base_datos = db.query(BaseDeDatos).filter(BaseDeDatos.id_base_datos == respaldo.id_base_datos).first()
    if not base_datos:
        raise HTTPException(status_code=400, detail="Base de datos no asociada al respaldo")
        
    instancia = db.query(InstanciaDBMS).filter(InstanciaDBMS.id_instancia == base_datos.id_instancia).first()
    if not instancia:
        raise HTTPException(status_code=400, detail="Instancia DBMS no asociada")
        
    servidor = db.query(Servidor).filter(Servidor.id_servidor == instancia.id_servidor).first()
    if not servidor:
        raise HTTPException(status_code=400, detail="Servidor no asociado")
        
    # Buscar credencial SSH del servidor
    credencial = db.query(CredencialAcceso).filter(
        CredencialAcceso.id_servidor == servidor.id_servidor,
        CredencialAcceso.id_tipo_acceso == 1 # Acceso SSH
    ).first()
    
    if not credencial:
        # Fallback a la credencial asociada al respaldo si existe
        if respaldo.id_credencial:
            credencial = db.query(CredencialAcceso).filter(CredencialAcceso.id_credencial == respaldo.id_credencial).first()
            
    if not credencial:
        raise HTTPException(status_code=400, detail="No se encontró credencial SSH para conectarse al servidor")

    # Asegurar que el directorio local exista
    os.makedirs(LOCAL_BACKUPS_DIR, exist_ok=True)
    local_path = os.path.join(LOCAL_BACKUPS_DIR, respaldo.nombre_archivo)

    # Iniciar conexión SSH
    client = get_ssh_connection(servidor, credencial, use_pool=True)
    sftp = None
    try:
        sftp = client.open_sftp()
        # Descargar archivo
        sftp.get(respaldo.path_fisico_origen, local_path)
        
        # Calcular hash local para verificar integridad
        local_hash = None
        hasher = None
        
        # Determinar algoritmo basado en longitud de hash registrado o por defecto sha256
        if respaldo.hash_integridad:
            if len(respaldo.hash_integridad) == 32:
                hasher = hashlib.md5()
            else:
                hasher = hashlib.sha256()
        else:
            hasher = hashlib.sha256()
            
        with open(local_path, 'rb') as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hasher.update(chunk)
        local_hash = hasher.hexdigest()
        
        # Comparar hashes si existe el original
        if respaldo.hash_integridad and respaldo.hash_integridad != local_hash:
            # Eliminar archivo corrupto
            if os.path.exists(local_path):
                os.remove(local_path)
            raise HTTPException(
                status_code=400, 
                detail=f"Fallo de integridad: hash local ({local_hash}) no coincide con el registrado ({respaldo.hash_integridad})"
            )
            
        # Si no tenía hash original, guardamos el nuevo hash local
        if not respaldo.hash_integridad:
            respaldo.hash_integridad = local_hash
            
        # Actualizar datos del respaldo
        respaldo.ubicacion_actual = "Descargado"
        respaldo.ip_almacenado_actual = "127.0.0.1" # Backend Local
        respaldo.path_fisico_actual = local_path
        respaldo.fecha_fin = datetime.now()
        
        # Registrar en bitácora
        bitacora = Bitacora(
            entidad_afectada="Respaldo",
            id_entidad=respaldo.id_respaldo,
            descripcion_evento=f"Descarga SFTP local exitosa del respaldo '{respaldo.nombre_archivo}' desde {servidor.direccion_ip}.",
            id_usuario=user_id,
            id_tipo_evento=5 # Ejecución
        )
        db.add(bitacora)
        db.commit()
        db.refresh(respaldo)
        
        return {
            "success": True,
            "message": "Respaldo descargado exitosamente a almacenamiento local",
            "local_path": local_path,
            "hash": local_hash
        }
    except Exception as e:
        db.rollback()
        # Limpieza ante errores
        if os.path.exists(local_path):
            os.remove(local_path)
        logger.error(f"Error al descargar respaldo por SFTP: {str(e)}")
        if isinstance(e, HTTPException):
            raise e
        raise HTTPException(status_code=500, detail=f"Error en transferencia SFTP: {str(e)}")
    finally:
        if sftp:
            sftp.close()

def replicate_to_external(db: Session, respaldo_id: int, destino_ruta_id: int, user_id: int) -> dict:
    """
    Replica un respaldo desde el servidor origen hacia un servidor SFTP externo (Modo Bridge).
    """
    respaldo = db.query(Respaldo).filter(Respaldo.id_respaldo == respaldo_id).first()
    if not respaldo:
        raise HTTPException(status_code=404, detail="Respaldo no encontrado")
        
    ruta_dest = db.query(RutaRespaldo).filter(RutaRespaldo.id_ruta == destino_ruta_id).first()
    if not ruta_dest:
        raise HTTPException(status_code=404, detail="Ruta de destino externa no encontrada")
        
    # Obtener servidor origen
    base_datos = db.query(BaseDeDatos).filter(BaseDeDatos.id_base_datos == respaldo.id_base_datos).first()
    if not base_datos:
        raise HTTPException(status_code=400, detail="Base de datos no asociada al respaldo")
    instancia_src = db.query(InstanciaDBMS).filter(InstanciaDBMS.id_instancia == base_datos.id_instancia).first()
    servidor_src = db.query(Servidor).filter(Servidor.id_servidor == instancia_src.id_servidor).first()
    cred_src = db.query(CredencialAcceso).filter(
        CredencialAcceso.id_servidor == servidor_src.id_servidor,
        CredencialAcceso.id_tipo_acceso == 1
    ).first()
    
    if not cred_src and respaldo.id_credencial:
        cred_src = db.query(CredencialAcceso).filter(CredencialAcceso.id_credencial == respaldo.id_credencial).first()
        
    if not cred_src:
        raise HTTPException(status_code=400, detail="No se encontró credencial SSH origen")

    # Obtener servidor destino
    servidor_dst = ruta_dest.servidor
    cred_dst = db.query(CredencialAcceso).filter(
        CredencialAcceso.id_servidor == servidor_dst.id_servidor,
        CredencialAcceso.id_tipo_acceso == 1
    ).first()
    if not cred_dst:
        raise HTTPException(status_code=400, detail="No se encontró credencial SSH destino")

    # Descarga temporal
    temp_dir = os.path.join(LOCAL_BACKUPS_DIR, "temp")
    os.makedirs(temp_dir, exist_ok=True)
    temp_local_path = os.path.join(temp_dir, respaldo.nombre_archivo)
    
    # 1. Conexión Origen -> Descargar
    client_src = get_ssh_connection(servidor_src, cred_src, use_pool=True)
    sftp_src = None
    sftp_dst = None
    try:
        sftp_src = client_src.open_sftp()
        sftp_src.get(respaldo.path_fisico_origen, temp_local_path)
        
        # Calcular/verificar hash
        local_hash = None
        hasher = hashlib.md5() if (respaldo.hash_integridad and len(respaldo.hash_integridad) == 32) else hashlib.sha256()
        with open(temp_local_path, 'rb') as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hasher.update(chunk)
        local_hash = hasher.hexdigest()
        
        if respaldo.hash_integridad and respaldo.hash_integridad != local_hash:
            raise HTTPException(status_code=400, detail="Fallo de integridad en descarga origen")
            
        if not respaldo.hash_integridad:
            respaldo.hash_integridad = local_hash

        # 2. Conexión Destino -> Subir
        client_dst = get_ssh_connection(servidor_dst, cred_dst, use_pool=True)
        sftp_dst = client_dst.open_sftp()
        
        # Construir ruta final de destino
        remote_dest_path = f"{ruta_dest.path}/{respaldo.nombre_archivo}".replace("//", "/")
        sftp_dst.put(temp_local_path, remote_dest_path)
        
        # Actualizar datos
        respaldo.ubicacion_actual = "Replica"
        respaldo.ip_almacenado_actual = servidor_dst.direccion_ip
        respaldo.path_fisico_actual = remote_dest_path
        respaldo.fecha_fin = datetime.now()
        
        bitacora = Bitacora(
            entidad_afectada="Respaldo",
            id_entidad=respaldo.id_respaldo,
            descripcion_evento=f"Replicación SFTP exitosa de '{respaldo.nombre_archivo}' desde {servidor_src.direccion_ip} hacia {servidor_dst.direccion_ip} en {remote_dest_path}.",
            id_usuario=user_id,
            id_tipo_evento=5
        )
        db.add(bitacora)
        db.commit()
        db.refresh(respaldo)
        
        return {
            "success": True,
            "message": "Respaldo replicado exitosamente al servidor externo",
            "destination_ip": servidor_dst.direccion_ip,
            "destination_path": remote_dest_path,
            "hash": local_hash
        }
    except Exception as e:
        db.rollback()
        logger.error(f"Error en replicación SFTP externa: {str(e)}")
        if isinstance(e, HTTPException):
            raise e
        raise HTTPException(status_code=500, detail=f"Error en replicación: {str(e)}")
    finally:
        if sftp_src:
            sftp_src.close()
        if sftp_dst:
            sftp_dst.close()
        if os.path.exists(temp_local_path):
            os.remove(temp_local_path)


def download_raw_to_local(db: Session, servidor_id: int, credencial_id: int, remote_path: str, user_id: int) -> dict:
    """
    Descarga cualquier archivo remoto por SFTP al almacenamiento local del backend usando la ruta directa.
    """
    servidor = db.query(Servidor).filter(Servidor.id_servidor == servidor_id).first()
    credencial = db.query(CredencialAcceso).filter(CredencialAcceso.id_credencial == credencial_id).first()
    
    if not servidor or not credencial:
        raise HTTPException(status_code=404, detail="Servidor o Credencial no encontrados")
        
    file_name = remote_path.split('/')[-1]
    os.makedirs(LOCAL_BACKUPS_DIR, exist_ok=True)
    local_path = os.path.join(LOCAL_BACKUPS_DIR, file_name)

    # Iniciar conexión SSH
    client = get_ssh_connection(servidor, credencial, use_pool=True)
    sftp = None
    try:
        sftp = client.open_sftp()
        sftp.get(remote_path, local_path)
        
        # Calcular hash local
        hasher = hashlib.sha256()
        with open(local_path, 'rb') as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hasher.update(chunk)
        local_hash = hasher.hexdigest()
        
        # Registrar en bitácora
        bitacora = Bitacora(
            entidad_afectada="Respaldo (Directo)",
            id_entidad=servidor_id,
            descripcion_evento=f"Descarga SFTP directa exitosa del archivo '{file_name}' desde {servidor.direccion_ip} a {local_path}.",
            id_usuario=user_id,
            id_tipo_evento=5
        )
        db.add(bitacora)
        db.commit()
        
        return {
            "success": True,
            "message": "Archivo remoto descargado exitosamente por ruta directa",
            "local_path": local_path,
            "hash": local_hash
        }
    except Exception as e:
        db.rollback()
        if os.path.exists(local_path):
            os.remove(local_path)
        logger.error(f"Error en descarga SFTP directa: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error en transferencia directa SFTP: {str(e)}")
    finally:
        if sftp:
            sftp.close()

def replicate_raw_to_external(db: Session, servidor_id: int, credencial_id: int, remote_path: str, destino_ruta_id: int, user_id: int) -> dict:
    """
    Replica un archivo remoto por SFTP hacia un servidor SFTP externo (Modo Bridge) usando ruta directa.
    """
    servidor_src = db.query(Servidor).filter(Servidor.id_servidor == servidor_id).first()
    cred_src = db.query(CredencialAcceso).filter(CredencialAcceso.id_credencial == credencial_id).first()
    ruta_dest = db.query(RutaRespaldo).filter(RutaRespaldo.id_ruta == destino_ruta_id).first()
    
    if not servidor_src or not cred_src or not ruta_dest:
        raise HTTPException(status_code=404, detail="Servidor origen, Credencial o Ruta destino no encontrados")
        
    servidor_dst = ruta_dest.servidor
    cred_dst = db.query(CredencialAcceso).filter(
        CredencialAcceso.id_servidor == servidor_dst.id_servidor,
        CredencialAcceso.id_tipo_acceso == 1
    ).first()
    if not cred_dst:
        raise HTTPException(status_code=400, detail="No se encontró credencial SSH destino")

    file_name = remote_path.split('/')[-1]
    temp_dir = os.path.join(LOCAL_BACKUPS_DIR, "temp")
    os.makedirs(temp_dir, exist_ok=True)
    temp_local_path = os.path.join(temp_dir, file_name)
    
    client_src = get_ssh_connection(servidor_src, cred_src, use_pool=True)
    sftp_src = None
    sftp_dst = None
    try:
        # Descarga origen
        sftp_src = client_src.open_sftp()
        sftp_src.get(remote_path, temp_local_path)
        
        # Calcular hash
        hasher = hashlib.sha256()
        with open(temp_local_path, 'rb') as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hasher.update(chunk)
        local_hash = hasher.hexdigest()

        # Subida destino
        client_dst = get_ssh_connection(servidor_dst, cred_dst, use_pool=True)
        sftp_dst = client_dst.open_sftp()
        remote_dest_path = f"{ruta_dest.path}/{file_name}".replace("//", "/")
        sftp_dst.put(temp_local_path, remote_dest_path)
        
        bitacora = Bitacora(
            entidad_afectada="Respaldo (Directo)",
            id_entidad=servidor_id,
            descripcion_evento=f"Replicación directa SFTP exitosa de '{file_name}' desde {servidor_src.direccion_ip} hacia {servidor_dst.direccion_ip} en {remote_dest_path}.",
            id_usuario=user_id,
            id_tipo_evento=5
        )
        db.add(bitacora)
        db.commit()
        
        return {
            "success": True,
            "message": "Archivo remoto replicado exitosamente al servidor externo por ruta directa",
            "destination_ip": servidor_dst.direccion_ip,
            "destination_path": remote_dest_path,
            "hash": local_hash
        }
    except Exception as e:
        db.rollback()
        logger.error(f"Error en replicación directa SFTP externa: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error en replicación directa: {str(e)}")
    finally:
        if sftp_src:
            sftp_src.close()
        if sftp_dst:
            sftp_dst.close()
        if os.path.exists(temp_local_path):
            os.remove(temp_local_path)

