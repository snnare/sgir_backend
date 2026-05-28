import csv
import io
from sqlalchemy.orm import Session
from app.models.infrastructure_models import Servidor, CredencialAcceso, InstanciaDBMS, NivelCriticidad, TipoAcceso, DBMS, ServidorParticion, BaseDeDatos
from app.models.backup_models import RutaRespaldo, PoliticaRespaldo, AsignacionPoliticaBD, TipoRespaldo, TipoAlmacenamiento
from app.models.user_models import UserStatus
from app.models.audit_model import Bitacora
from app.core.security.encryption import encrypt_password
from typing import List, Dict, Any
from datetime import time

def normalize_text(text: str) -> str:
    """Normaliza texto para facilitar el matching (minúsculas y sin espacios extra)."""
    if not text:
        return ""
    return text.strip().lower()

def get_catalogs(db: Session) -> Dict[str, Dict[str, int]]:
    """Carga los catálogos en memoria para un mapeo rápido label -> ID."""
    catalogs = {
        "criticidad": {normalize_text(n.nombre_nivel): n.id_nivel_criticidad for n in db.query(NivelCriticidad).all()},
        "dbms": {normalize_text(d.nombre_dbms): d.id_dbms for d in db.query(DBMS).all()},
        "acceso": {normalize_text(t.nombre_tipo): t.id_tipo_acceso for t in db.query(TipoAcceso).all()},
        "estado": {normalize_text(e.nombre_estado): e.id_estado for e in db.query(UserStatus).all()},
        "tipo_respaldo": {normalize_text(r.nombre_tipo): r.id_tipo_respaldo for r in db.query(TipoRespaldo).all()},
        "tipo_almacenamiento": {normalize_text(a.nombre_tipo): a.id_tipo_almacenamiento for a in db.query(TipoAlmacenamiento).all()}
    }
    return catalogs

def process_infrastructure_csv(db: Session, file_content: bytes, user_id: int) -> Dict:
    """
    Procesa un archivo CSV para importar Servidores, Instancias y Credenciales.
    Maneja duplicados y vinculaciones automáticas.
    """
    stream = io.StringIO(file_content.decode("utf-8"))
    reader = csv.DictReader(stream)
    
    catalogs = get_catalogs(db)
    
    summary = {
        "total_filas": 0,
        "servidores_procesados": 0,
        "instancias_procesadas": 0,
        "credenciales_procesadas": 0,
        "errores": []
    }
    
    # Cache temporal para no re-consultar servidores creados en el mismo CSV
    processed_ips = {} # {direccion_ip: id_servidor}

    for i, row in enumerate(reader, start=1):
        summary["total_filas"] += 1
        try:
            ip = row.get("direccion_ip", "").strip()
            if not ip:
                summary["errores"].append({"fila": i, "error": "IP vacía"})
                continue

            # 1. TRADUCCIÓN DE IDs
            criticidad_id = catalogs["criticidad"].get(normalize_text(row.get("nivel_criticidad")))
            estado_id = catalogs["estado"].get(normalize_text(row.get("estado")), 1) # Default Activo (ID 1)
            dbms_id = catalogs["dbms"].get(normalize_text(row.get("nombre_dbms")))
            tipo_acceso_id = catalogs["acceso"].get(normalize_text(row.get("tipo_acceso")))

            if not criticidad_id:
                summary["errores"].append({"fila": i, "error": f"Nivel de criticidad '{row.get('nivel_criticidad')}' no reconocido"})
                continue

            # 2. MANEJO DE SERVIDOR
            servidor = db.query(Servidor).filter(Servidor.direccion_ip == ip).first()
            if not servidor:
                if ip in processed_ips:
                    servidor_id = processed_ips[ip]
                else:
                    # Crear nuevo servidor
                    nuevo_srv = Servidor(
                        nombre_servidor=row.get("nombre_servidor"),
                        direccion_ip=ip,
                        es_legacy=row.get("es_legacy", "false").lower() == "true",
                        descripcion=row.get("descripcion"),
                        id_nivel_criticidad=criticidad_id,
                        id_estado_servidor=estado_id
                    )
                    db.add(nuevo_srv)
                    db.flush() # Para obtener el ID
                    servidor_id = nuevo_srv.id_servidor
                    processed_ips[ip] = servidor_id
                    summary["servidores_procesados"] += 1
            else:
                servidor_id = servidor.id_servidor
                processed_ips[ip] = servidor_id

            # 2.1 MANEJO DE PARTICIONES
            paths_raw = row.get("particiones") or row.get("paths")
            
            # Si está vacío o no existe, por defecto es la raíz /
            if not paths_raw or not paths_raw.strip():
                paths_raw = "/"

            # Limpiar formato (path1, path2)
            clean_paths = paths_raw.strip()
            if clean_paths.startswith('(') and clean_paths.endswith(')'):
                clean_paths = clean_paths[1:-1]
            
            paths_list = [p.strip() for p in clean_paths.split(',') if p.strip()]
            
            for p_path in paths_list:
                # Evitar duplicados para este servidor
                exists = db.query(ServidorParticion).filter(
                    ServidorParticion.id_servidor == servidor_id,
                    ServidorParticion.path == p_path
                ).first()
                
                if not exists:
                    nueva_part = ServidorParticion(
                        id_servidor=servidor_id,
                        path=p_path,
                        etiqueta="Importado"
                    )
                    db.add(nueva_part)

            # 3. MANEJO DE INSTANCIA (Si hay datos de DBMS e Instancia)
            instancia_id = None
            if dbms_id and row.get("nombre_instancia"):
                instancia = db.query(InstanciaDBMS).filter(
                    InstanciaDBMS.id_servidor == servidor_id,
                    InstanciaDBMS.nombre_instancia == row.get("nombre_instancia")
                ).first()
                
                if not instancia:
                    nueva_inst = InstanciaDBMS(
                        nombre_instancia=row.get("nombre_instancia"),
                        puerto=int(row.get("puerto_db", 0)),
                        id_servidor=servidor_id,
                        id_dbms=dbms_id,
                        id_estado_instancia=estado_id
                    )
                    db.add(nueva_inst)
                    db.flush()
                    instancia_id = nueva_inst.id_instancia
                    summary["instancias_procesadas"] += 1
                else:
                    instancia_id = instancia.id_instancia

            # 4. MANEJO DE CREDENCIAL
            if tipo_acceso_id and row.get("usuario") and row.get("password"):
                # Verificar si ya existe esa credencial (usuario + tipo + servidor)
                cred_existente = db.query(CredencialAcceso).filter(
                    CredencialAcceso.id_servidor == servidor_id,
                    CredencialAcceso.usuario == row.get("usuario"),
                    CredencialAcceso.id_tipo_acceso == tipo_acceso_id
                ).first()

                if not cred_existente:
                    nueva_cred = CredencialAcceso(
                        usuario=row.get("usuario"),
                        password_hash=encrypt_password(row.get("password")),
                        id_tipo_acceso=tipo_acceso_id,
                        id_estado_credencial=estado_id,
                        id_servidor=servidor_id
                    )
                    db.add(nueva_cred)
                    summary["credenciales_procesadas"] += 1

        except Exception as e:
            db.rollback()
            summary["errores"].append({"fila": i, "error": str(e)})
            continue

    # 5. FINALIZAR Y AUDITAR
    if summary["servidores_procesados"] > 0 or summary["credenciales_procesadas"] > 0:
        db.commit()
        # Auditoría masiva
        audit = Bitacora(
            entidad_afectada="Infraestructura (Bulk)",
            id_entidad=user_id,
            descripcion_evento=f"Importación masiva: {summary['servidores_procesados']} srv, {summary['instancias_procesadas']} inst, {summary['credenciales_procesadas']} cred.",
            id_usuario=user_id,
            id_tipo_evento=2 # Creación
        )
        db.add(audit)
        db.commit()
    
    return summary


def process_rutas_respaldo_csv(db: Session, file_content: bytes, user_id: int) -> Dict:
    """
    Procesa un archivo CSV para importar Rutas de Respaldo vinculándolas a servidores.
    """
    stream = io.StringIO(file_content.decode("utf-8"))
    reader = csv.DictReader(stream)
    catalogs = get_catalogs(db)
    
    summary = {
        "total_filas": 0,
        "rutas_procesadas": 0,
        "errores": []
    }
    
    for i, row in enumerate(reader, start=1):
        summary["total_filas"] += 1
        try:
            ip = row.get("direccion_ip", "").strip()
            path = row.get("path", "").strip()
            
            if not ip or not path:
                summary["errores"].append({"fila": i, "error": "IP del servidor o Path vacío"})
                continue
                
            # 1. Buscar servidor en CMDB
            srv = db.query(Servidor).filter(Servidor.direccion_ip == ip).first()
            if not srv:
                summary["errores"].append({"fila": i, "error": f"Servidor con IP '{ip}' no encontrado en CMDB"})
                continue
                
            # 2. Traducir catálogos
            almacenamiento_id = catalogs["tipo_almacenamiento"].get(normalize_text(row.get("tipo_almacenamiento")))
            estado_id = catalogs["estado"].get(normalize_text(row.get("estado")), 1)
            
            if not almacenamiento_id:
                summary["errores"].append({"fila": i, "error": f"Tipo de almacenamiento '{row.get('tipo_almacenamiento')}' no reconocido"})
                continue
                
            # 3. Evitar duplicados
            exists = db.query(RutaRespaldo).filter(
                RutaRespaldo.id_servidor == srv.id_servidor,
                RutaRespaldo.path == path
            ).first()
            
            if not exists:
                nueva_ruta = RutaRespaldo(
                    descripcion_ruta=row.get("descripcion_ruta", "Ruta Importada"),
                    path=path,
                    id_servidor=srv.id_servidor,
                    id_tipo_almacenamiento=almacenamiento_id,
                    id_estado_ruta=estado_id
                )
                db.add(nueva_ruta)
                summary["rutas_procesadas"] += 1
                
        except Exception as e:
            db.rollback()
            summary["errores"].append({"fila": i, "error": str(e)})
            continue
            
    if summary["rutas_procesadas"] > 0:
        db.commit()
        audit = Bitacora(
            entidad_afectada="RutaRespaldo (Bulk)",
            id_entidad=user_id,
            descripcion_evento=f"Importación masiva: {summary['rutas_procesadas']} rutas de respaldo creadas.",
            id_usuario=user_id,
            id_tipo_evento=2
        )
        db.add(audit)
        db.commit()
        
    return summary


def process_bases_datos_csv(db: Session, file_content: bytes, user_id: int) -> Dict:
    """
    Procesa un archivo CSV para importar Bases de Datos asociadas a una Instancia de DBMS.
    """
    stream = io.StringIO(file_content.decode("utf-8"))
    reader = csv.DictReader(stream)
    catalogs = get_catalogs(db)
    
    summary = {
        "total_filas": 0,
        "bases_procesadas": 0,
        "errores": []
    }
    
    for i, row in enumerate(reader, start=1):
        summary["total_filas"] += 1
        try:
            ip = row.get("direccion_ip", "").strip()
            puerto = row.get("puerto_db", "").strip()
            nombre_instancia = row.get("nombre_instancia", "").strip()
            nombre_base = row.get("nombre_base", "").strip()
            
            if not ip or not puerto or not nombre_instancia or not nombre_base:
                summary["errores"].append({"fila": i, "error": "IP, Puerto, Instancia o Base de datos vacíos"})
                continue
                
            # 1. Buscar la instancia DBMS
            instancia = db.query(InstanciaDBMS).join(Servidor).filter(
                Servidor.direccion_ip == ip,
                InstanciaDBMS.puerto == int(puerto),
                InstanciaDBMS.nombre_instancia == nombre_instancia
            ).first()
            
            if not instancia:
                summary["errores"].append({"fila": i, "error": f"Instancia '{nombre_instancia}' en IP '{ip}': '{puerto}' no encontrada"})
                continue
                
            # 2. Traducir catálogo
            estado_id = catalogs["estado"].get(normalize_text(row.get("estado")), 1)
            
            # 3. Evitar duplicados
            exists = db.query(BaseDeDatos).filter(
                BaseDeDatos.id_instancia == instancia.id_instancia,
                BaseDeDatos.nombre_base == nombre_base
            ).first()
            
            if not exists:
                tamano = row.get("tamano_mb")
                nueva_bd = BaseDeDatos(
                    nombre_base=nombre_base,
                    tamano_mb=float(tamano) if tamano else None,
                    id_instancia=instancia.id_instancia,
                    id_estado_bd=estado_id
                )
                db.add(nueva_bd)
                summary["bases_procesadas"] += 1
                
        except Exception as e:
            db.rollback()
            summary["errores"].append({"fila": i, "error": str(e)})
            continue
            
    if summary["bases_procesadas"] > 0:
        db.commit()
        audit = Bitacora(
            entidad_afectada="BaseDeDatos (Bulk)",
            id_entidad=user_id,
            descripcion_evento=f"Importación masiva: {summary['bases_procesadas']} bases de datos registradas.",
            id_usuario=user_id,
            id_tipo_evento=2
        )
        db.add(audit)
        db.commit()
        
    return summary


def process_politicas_respaldo_csv(db: Session, file_content: bytes, user_id: int) -> Dict:
    """
    Procesa un archivo CSV para importar Políticas de Respaldo.
    """
    stream = io.StringIO(file_content.decode("utf-8"))
    reader = csv.DictReader(stream)
    catalogs = get_catalogs(db)
    
    summary = {
        "total_filas": 0,
        "politicas_procesadas": 0,
        "errores": []
    }
    
    for i, row in enumerate(reader, start=1):
        summary["total_filas"] += 1
        try:
            nombre = row.get("nombre_politica", "").strip()
            frecuencia = row.get("frecuencia_horas", "").strip()
            retencion = row.get("retencion_dias", "").strip()
            tipo_respaldo_str = row.get("tipo_respaldo", "").strip()
            
            if not nombre or not frecuencia or not retencion or not tipo_respaldo_str:
                summary["errores"].append({"fila": i, "error": "Nombre, Frecuencia, Retención o Tipo de Respaldo vacíos"})
                continue
                
            # 1. Traducir catálogos
            tipo_resp_id = catalogs["tipo_respaldo"].get(normalize_text(tipo_respaldo_str))
            estado_id = catalogs["estado"].get(normalize_text(row.get("estado")), 1)
            
            if not tipo_resp_id:
                summary["errores"].append({"fila": i, "error": f"Tipo de respaldo '{tipo_respaldo_str}' no reconocido"})
                continue
                
            # 2. Evitar duplicados
            exists = db.query(PoliticaRespaldo).filter(PoliticaRespaldo.nombre_politica == nombre).first()
            if not exists:
                hora_str = row.get("hora_ejecuccion")
                hora_val = None
                if hora_str and hora_str.strip():
                    try:
                        from datetime import datetime
                        hora_val = datetime.strptime(hora_str.strip(), "%H:%M:%S").time()
                    except ValueError:
                        try:
                            hora_val = datetime.strptime(hora_str.strip(), "%H:%M").time()
                        except ValueError:
                            pass
                            
                nueva_pol = PoliticaRespaldo(
                    nombre_politica=nombre,
                    descripcion=row.get("descripcion"),
                    expression_cron=row.get("expression_cron") if row.get("expression_cron") else None,
                    hora_ejecuccion=hora_val,
                    dias_semana=row.get("dias_semana") if row.get("dias_semana") else None,
                    frecuencia_horas=int(frecuencia),
                    retencion_dias=int(retencion),
                    script_path=row.get("script_path") if row.get("script_path") else None,
                    id_tipo_respaldo=tipo_resp_id,
                    id_estado_politica=estado_id
                )
                db.add(nueva_pol)
                summary["politicas_procesadas"] += 1
                
        except Exception as e:
            db.rollback()
            summary["errores"].append({"fila": i, "error": str(e)})
            continue
            
    if summary["politicas_procesadas"] > 0:
        db.commit()
        audit = Bitacora(
            entidad_afectada="PoliticaRespaldo (Bulk)",
            id_entidad=user_id,
            descripcion_evento=f"Importación masiva: {summary['politicas_procesadas']} políticas de respaldo creadas.",
            id_usuario=user_id,
            id_tipo_evento=2
        )
        db.add(audit)
        db.commit()
        
    return summary


def process_asignaciones_politica_csv(db: Session, file_content: bytes, user_id: int) -> Dict:
    """
    Procesa un archivo CSV para importar Asignaciones de Políticas a Bases de Datos.
    """
    stream = io.StringIO(file_content.decode("utf-8"))
    reader = csv.DictReader(stream)
    
    summary = {
        "total_filas": 0,
        "asignaciones_procesadas": 0,
        "errores": []
    }
    
    for i, row in enumerate(reader, start=1):
        summary["total_filas"] += 1
        try:
            ip = row.get("direccion_ip", "").strip()
            puerto = row.get("puerto_db", "").strip()
            nombre_instancia = row.get("nombre_instancia", "").strip()
            nombre_base = row.get("nombre_base", "").strip()
            nombre_politica = row.get("nombre_politica", "").strip()
            
            if not ip or not puerto or not nombre_instancia or not nombre_base or not nombre_politica:
                summary["errores"].append({"fila": i, "error": "IP, Puerto, Instancia, Base de datos o Política vacíos"})
                continue
                
            # 1. Buscar la Base de Datos
            bd = db.query(BaseDeDatos).join(InstanciaDBMS).join(Servidor).filter(
                Servidor.direccion_ip == ip,
                InstanciaDBMS.puerto == int(puerto),
                InstanciaDBMS.nombre_instancia == nombre_instancia,
                BaseDeDatos.nombre_base == nombre_base
            ).first()
            
            if not bd:
                summary["errores"].append({"fila": i, "error": f"Base de datos '{nombre_base}' en Instancia '{nombre_instancia}' (IP: '{ip}') no encontrada"})
                continue
                
            # 2. Buscar la Política
            politica = db.query(PoliticaRespaldo).filter(PoliticaRespaldo.nombre_politica == nombre_politica).first()
            if not politica:
                summary["errores"].append({"fila": i, "error": f"Política '{nombre_politica}' no encontrada"})
                continue
                
            # 3. Evitar duplicados
            exists = db.query(AsignacionPoliticaBD).filter(
                AsignacionPoliticaBD.id_base_datos == bd.id_base_datos,
                AsignacionPoliticaBD.id_politica == politica.id_politica
            ).first()
            
            if not exists:
                nueva_asig = AsignacionPoliticaBD(
                    id_base_datos=bd.id_base_datos,
                    id_politica=politica.id_politica
                )
                db.add(nueva_asig)
                summary["asignaciones_procesadas"] += 1
                
        except Exception as e:
            db.rollback()
            summary["errores"].append({"fila": i, "error": str(e)})
            continue
            
    if summary["asignaciones_procesadas"] > 0:
        db.commit()
        audit = Bitacora(
            entidad_afectada="AsignacionPoliticaBD (Bulk)",
            id_entidad=user_id,
            descripcion_evento=f"Importación masiva: {summary['asignaciones_procesadas']} asignaciones de políticas realizadas.",
            id_usuario=user_id,
            id_tipo_evento=2
        )
        db.add(audit)
        db.commit()
        
    return summary
