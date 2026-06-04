from sqlalchemy.orm import Session
from sqlalchemy import text
from app.models.infrastructure_models import BaseDeDatos, InstanciaDBMS, CredencialAcceso
from app.core.dynamic_db_core import get_dynamic_session
from app.services.infrastructure import infrastructure_crud
get_instancia = infrastructure_crud.get_instancia
get_servidor = infrastructure_crud.get_servidor

def get_mysql_remote_databases(session):
    """
    Ejecuta la consulta de descubrimiento en una instancia MySQL (5 o 8).
    Retorna: nombre_db, tamanio_mb, fecha_creacion.
    """
    query = text("""
        SELECT 
            s.schema_name AS nombre_db,
            COALESCE(SUM(t.data_length + t.index_length) / 1024 / 1024, 0) AS tamanio_mb,
            MIN(t.create_time) AS fecha_creacion
        FROM information_schema.SCHEMATA s
        LEFT JOIN information_schema.TABLES t ON s.schema_name = t.table_schema
        WHERE s.schema_name NOT IN ('information_schema', 'mysql', 'performance_schema', 'sys')
        GROUP BY s.schema_name;
    """)
    
    result = session.execute(query)
    databases = []
    for row in result:
        databases.append({
            "nombre": row[0],
            "tamano_mb": float(row[1]),
            "fecha_creacion": row[2]
        })
    return databases

def get_oracle_remote_databases(session):
    """
    Ejecuta la consulta de descubrimiento en una instancia Oracle.
    Filtra esquemas de sistema comunes.
    """
    query = text("""
        SELECT 
            username AS nombre_db,
            0 AS tamano_mb,
            created AS fecha_creacion
        FROM all_users
        WHERE username NOT IN (
            'SYS', 'SYSTEM', 'DBSNMP', 'OUTLN', 'APPQOSSYS', 'CTXSYS', 'ANONYMOUS', 
            'WMSYS', 'XDB', 'ORDDATA', 'ORDSYS', 'MDSYS', 'OLAPSYS', 'MDDATA', 
            'SPATIAL_WFS_ADMIN_USR', 'SPATIAL_CSW_ADMIN_USR', 'APEX_040200', 
            'GSMADMIN_INTERNAL', 'LBACSYS', 'DVSYS', 'DVF', 'AUDSYS', 'GSMUSER', 
            'GGSYS', 'APEX_PUBLIC_USER', 'FLOWS_FILES', 'APEX_030200', 'MGMT_VIEW', 
            'OWBSYS', 'OWBSYS_AUDIT', 'SI_INFORMTN_SCHEMA', 'ORDPLUGINS'
        )
        ORDER BY username
    """)
    
    result = session.execute(query)
    databases = []
    for row in result:
        databases.append({
            "nombre": row[0],
            "tamano_mb": float(row[1]),
            "fecha_creacion": row[2]
        })
    return databases

def get_mongodb_remote_databases(client):
    """
    Usa el cliente de MongoDB para listar bases de datos y sus tamaños.
    """
    databases = []
    # list_database_names() requiere privilegios, similar a listDatabases
    for db_name in client.list_database_names():
        if db_name not in ['admin', 'config', 'local']:
            try:
                stats = client[db_name].command("dbStats")
                databases.append({
                    "nombre": db_name,
                    "tamano_mb": round(stats.get("dataSize", 0) / 1024 / 1024, 2),
                    "fecha_creacion": None
                })
            except Exception:
                # Si no tiene permisos para dbStats, al menos traemos el nombre
                databases.append({
                    "nombre": db_name,
                    "tamano_mb": 0,
                    "fecha_creacion": None
                })
    return databases

def sync_databases_inventory(db: Session, instancia_id: int, credencial_id: int):
    """
    ORQUESTADOR DE AUTO-BÚSQUEDA Y SINCRONIZACIÓN:
    1. Conecta a la instancia remota usando la credencial elegida.
    2. Ejecuta query de descubrimiento según el tipo de DBMS.
    3. Actualiza o inserta en la tabla Base_de_Datos local.
    """
    instancia = get_instancia(db, instancia_id)
    servidor = get_servidor(db, instancia.id_servidor) if instancia else None
    credencial = db.query(CredencialAcceso).filter(CredencialAcceso.id_credencial == credencial_id).first()

    if not instancia or not servidor or not credencial:
        return {"error": "Instancia, Servidor o Credencial no encontrados"}

    # 1. Obtener lista remota según DBMS
    remote_dbs = []
    session_remota = None
    try:
        # 2, 3: MySQL, 4: Oracle, 5: MongoDB
        # CORRECCIÓN: Para MySQL descubrimiento, conectamos a information_schema.
        # Para Oracle/Mongo usamos el nombre de instancia/CDB normal.
        db_conn_name = "information_schema" if instancia.id_dbms in [2, 3] else instancia.nombre_instancia
        
        session_remota = get_dynamic_session(
            servidor, 
            credencial, 
            dbms_id=instancia.id_dbms, 
            db_name=db_conn_name, 
            parametros=instancia.parametros_conexion
        )
        
        if instancia.id_dbms in [2, 3]: # MySQL
            remote_dbs = get_mysql_remote_databases(session_remota)
        elif instancia.id_dbms == 4: # Oracle
            remote_dbs = get_oracle_remote_databases(session_remota)
        elif instancia.id_dbms == 5: # MongoDB
            remote_dbs = get_mongodb_remote_databases(session_remota)
        else:
            return {"error": f"DBMS ID {instancia.id_dbms} no soportado para auto-búsqueda actualmente"}
            
    except Exception as e:
        if instancia.id_dbms == 4:
            print(f"[Oracle Discovery Fallback] Conexión TCP falló ({str(e)}). Intentando fallback vía SSH/sqlplus...")
            try:
                from app.core.ssh_orchestrator import get_ssh_connection
                from app.core.security.encryption import decrypt_password
                from datetime import datetime
                
                # Buscar credencial SSH activa (id_tipo_acceso == 1)
                ssh_cred = db.query(CredencialAcceso).filter(
                    CredencialAcceso.id_servidor == servidor.id_servidor,
                    CredencialAcceso.id_tipo_acceso == 1,
                    CredencialAcceso.id_estado_credencial == 1
                ).first()
                
                if not ssh_cred:
                    return {"error": f"Fallo en conexión remota TCP ({str(e)}) y no se encontró credencial SSH activa para fallback."}
                
                ssh_client = get_ssh_connection(servidor, ssh_cred)
                db_user = credencial.usuario
                db_password = decrypt_password(credencial.password_hash)
                params = instancia.parametros_conexion or {}
                sid = params.get("sid") or instancia.nombre_instancia
                
                cmd = f"""cd /home/oracle && source .bash_profile
export ORACLE_SID={sid}
sqlplus -S '{db_user}/{db_password}' << 'EOF'
SET HEAD OFF FEEDBACK OFF ECHO OFF PAGESIZE 0 TRIMSPOOL ON;
SELECT username || '|' || to_char(created, 'YYYY-MM-DD HH24:MI:SS') FROM all_users
WHERE username NOT IN (
    'SYS', 'SYSTEM', 'DBSNMP', 'OUTLN', 'APPQOSSYS', 'CTXSYS', 'ANONYMOUS', 
    'WMSYS', 'XDB', 'ORDDATA', 'ORDSYS', 'MDSYS', 'OLAPSYS', 'MDDATA', 
    'SPATIAL_WFS_ADMIN_USR', 'SPATIAL_CSW_ADMIN_USR', 'APEX_040200', 
    'GSMADMIN_INTERNAL', 'LBACSYS', 'DVSYS', 'DVF', 'AUDSYS', 'GSMUSER', 
    'GGSYS', 'APEX_PUBLIC_USER', 'FLOWS_FILES', 'APEX_030200', 'MGMT_VIEW', 
    'OWBSYS', 'OWBSYS_AUDIT', 'SI_INFORMTN_SCHEMA', 'ORDPLUGINS'
)
ORDER BY username;
EXIT;
EOF
"""
                stdin, stdout, stderr = ssh_client.exec_command(cmd)
                output = stdout.read().decode('utf-8').strip()
                
                if not output or "ERROR" in output or "ORA-" in output:
                    return {"error": f"Fallo en conexión TCP ({str(e)}) y fallback SSH sqlplus retornó error: {output}"}
                
                for line in output.split('\n'):
                    if '|' in line:
                        parts = line.split('|')
                        try:
                            fecha_dt = datetime.strptime(parts[1].strip(), '%Y-%m-%d %H:%M:%S')
                        except:
                            fecha_dt = None
                        remote_dbs.append({
                            "nombre": parts[0].strip(),
                            "tamano_mb": 0.0,
                            "fecha_creacion": fecha_dt
                        })
            except Exception as ssh_err:
                return {"error": f"Fallo en conexión TCP ({str(e)}) y fallback SSH falló con error: {str(ssh_err)}"}
        else:
            return {"error": f"Fallo en conexión remota: {str(e)}"}
    finally:
        # En MongoDB session_remota es un MongoClient que manejamos vía pool ahora, 
        # pero get_dynamic_session devuelve la instancia del pool. 
        # No cerramos si es Mongo (manejado por pool)
        if session_remota and instancia.id_dbms != 5 and hasattr(session_remota, 'close'):
            session_remota.close()

    # 2. Sincronizar localmente (Upsert)
    sync_results = {
        "instancia": instancia.nombre_instancia,
        "total_encontradas": len(remote_dbs),
        "creadas": 0,
        "actualizadas": 0,
        "desactivadas": 0
    }
    
    remote_names = [d["nombre"] for d in remote_dbs]

    # Desactivar bases de datos que ya no existen en el remoto para esta instancia
    db.query(BaseDeDatos).filter(
        BaseDeDatos.id_instancia == instancia_id,
        BaseDeDatos.nombre_base.notin_(remote_names)
    ).update({"id_estado_bd": 2}, synchronize_session=False) # 2: Inactivo

    # Insertar o actualizar
    for r_db in remote_dbs:
        db_exists = db.query(BaseDeDatos).filter(
            BaseDeDatos.id_instancia == instancia_id,
            BaseDeDatos.nombre_base == r_db["nombre"]
        ).first()

        if db_exists:
            db_exists.tamano_mb = r_db["tamano_mb"]
            db_exists.id_estado_bd = 1 # Activo
            # Solo actualizamos fecha si el remoto la provee y la local es nula
            if r_db["fecha_creacion"] and not db_exists.fecha_creacion:
                db_exists.fecha_creacion = r_db["fecha_creacion"]
            sync_results["actualizadas"] += 1
        else:
            new_entry = BaseDeDatos(
                nombre_base=r_db["nombre"],
                tamano_mb=r_db["tamano_mb"],
                fecha_creacion=r_db["fecha_creacion"],
                id_instancia=instancia_id,
                id_estado_bd=1 # Activo
            )
            db.add(new_entry)
            sync_results["creadas"] += 1

    db.commit()
    return sync_results

def run_bulk_inventory_sync(db: Session):
    """
    Orquestador masivo que recorre todos los servidores con monitoreo_db activo
    y sincroniza sus bases de datos en paralelo.
    """
    from app.models.infrastructure_models import Servidor
    from app.core.scheduler_manager import scheduler_executor
    from app.db.postgres.postgres_connection import SessionLocal
    from concurrent.futures import as_completed

    # Fase 1: Descubrimiento en caliente de instancias Oracle (SIDs)
    servidores_activos = db.query(Servidor).filter(Servidor.monitoreo_db == True).all()
    for svr in servidores_activos:
        try:
            discover_and_register_oracle_instances(db, svr.id_servidor)
        except Exception as e:
            print(f"[Oracle Bulk Discovery] Error en servidor {svr.nombre_servidor}: {str(e)}")

    # Fase 2: Buscar todas las instancias de servidores que tengan monitoreo_db activo
    instancias = db.query(InstanciaDBMS).join(Servidor).filter(
        Servidor.monitoreo_db == True,
        InstanciaDBMS.id_estado_instancia == 1 # Activa
    ).all()

    summary = {
        "total_instancias_encontradas": len(instancias),
        "instancias_procesadas_exitosamente": 0,
        "instancias_fallidas": 0,
        "omitidas_sin_credenciales": 0,
        "detalles": [],
        "total_db_size_mb": 0.0
    }

    def worker_task(inst_id, cred_id):
        # Cada hilo debe manejar su propia sesión para ser thread-safe
        worker_db = SessionLocal()
        try:
            return sync_databases_inventory(worker_db, inst_id, cred_id)
        finally:
            worker_db.close()

    futures = {}
    
    for inst in instancias:
        # Buscar credencial DB Native activa (id_tipo_acceso = 2)
        cred = db.query(CredencialAcceso).filter(
            CredencialAcceso.id_servidor == inst.id_servidor,
            CredencialAcceso.id_tipo_acceso == 2,
            CredencialAcceso.id_estado_credencial == 1
        ).first()

        if cred:
            # Lanzamos al pool de hilos
            future = scheduler_executor.submit(worker_task, inst.id_instancia, cred.id_credencial)
            futures[future] = inst.nombre_instancia
        else:
            summary["omitidas_sin_credenciales"] += 1
            summary["detalles"].append({
                "instancia": inst.nombre_instancia,
                "status": "skipped",
                "error": "No se encontró credencial DB Native activa"
            })

    # 2. Esperar resultados y consolidar detalles
    for future in as_completed(futures):
        inst_name = futures[future]
        try:
            res = future.result()
            if isinstance(res, dict) and "error" in res:
                summary["instancias_fallidas"] += 1
                summary["detalles"].append({
                    "instancia": inst_name,
                    "status": "failed",
                    "error": res["error"]
                })
            else:
                summary["instancias_procesadas_exitosamente"] += 1
                summary["detalles"].append({
                    "instancia": inst_name,
                    "status": "success",
                    "nuevas": res.get("creadas", 0),
                    "actualizadas": res.get("actualizadas", 0),
                    "desactivadas": res.get("desactivadas", 0)
                })
        except Exception as e:
            summary["instancias_fallidas"] += 1
            summary["detalles"].append({
                "instancia": inst_name,
                "status": "error_critical",
                "error": str(e)
            })

    # 3. Calcular tamaño total real desde la tabla local después de la sincronización
    from sqlalchemy import func
    total_size = db.query(func.sum(BaseDeDatos.tamano_mb)).filter(BaseDeDatos.id_estado_bd == 1).scalar()
    summary["total_db_size_mb"] = float(total_size or 0)

    return summary


def discover_and_register_oracle_instances(db: Session, servidor_id: int):
    import re
    from app.models.infrastructure_models import Servidor, InstanciaDBMS, DBMS, CredencialAcceso
    from app.services.monitoring.ssh_service import get_ssh_connection

    servidor = db.query(Servidor).filter(Servidor.id_servidor == servidor_id).first()
    if not servidor:
        return []

    # 1. Buscar credencial SSH activa (id_tipo_acceso == 1, id_estado == 1)
    ssh_cred = db.query(CredencialAcceso).filter(
        CredencialAcceso.id_servidor == servidor_id,
        CredencialAcceso.id_tipo_acceso == 1,
        CredencialAcceso.id_estado_credencial == 1
    ).first()

    if not ssh_cred:
        print(f"[Oracle Discovery] No se encontró credencial SSH activa para el servidor {servidor.nombre_servidor}")
        return []

    # 2. Buscar DBMS para Oracle Database
    oracle_dbms = db.query(DBMS).filter(DBMS.nombre_dbms.ilike("%oracle%")).first()
    if not oracle_dbms:
        print("[Oracle Discovery] No se encontró el DBMS de tipo Oracle Database en el catálogo.")
        return []

    client = None
    try:
        client = get_ssh_connection(servidor, ssh_cred, use_pool=True)
        # Ejecutar comando para buscar procesos ora_smon activos
        stdin, stdout, stderr = client.exec_command("ps -ef | grep smon | grep -v grep")
        output = stdout.read().decode('utf-8').strip()
        
        if not output:
            return []

        discovered_sids = []
        for line in output.split('\n'):
            match = re.search(r'ora_smon_(.+)$', line.strip())
            if match:
                sid = match.group(1).strip()
                if sid not in discovered_sids:
                    discovered_sids.append(sid)

        created_instances = []
        for sid in discovered_sids:
            # Verificar si ya existe
            exists = db.query(InstanciaDBMS).filter(
                InstanciaDBMS.id_servidor == servidor_id,
                InstanciaDBMS.nombre_instancia.ilike(sid)
            ).first()

            if not exists:
                nueva_inst = InstanciaDBMS(
                    nombre_instancia=sid,
                    puerto=1521,  # Puerto Oracle estándar
                    id_servidor=servidor_id,
                    id_dbms=oracle_dbms.id_dbms,
                    id_estado_instancia=1,  # Activa
                    parametros_conexion={"sid": sid}
                )
                db.add(nueva_inst)
                created_instances.append(sid)

        if created_instances:
            db.commit()
            print(f"[Oracle Discovery] Nuevas instancias Oracle registradas para {servidor.direccion_ip}: {created_instances}")
        return created_instances
    except Exception as e:
        print(f"[Oracle Discovery] Error al escanear SIDs por SSH: {str(e)}")
        return []
