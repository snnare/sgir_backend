import csv
import io
from sqlalchemy.orm import Session
from app.models.infrastructure_models import Servidor, CredencialAcceso, InstanciaDBMS, NivelCriticidad, TipoAcceso, DBMS, ServidorParticion
from app.models.user_models import UserStatus
from app.models.audit_model import Bitacora
from app.core.security.encryption import encrypt_password
from typing import List, Dict

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
        "estado": {normalize_text(e.nombre_estado): e.id_estado for e in db.query(UserStatus).all()}
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
