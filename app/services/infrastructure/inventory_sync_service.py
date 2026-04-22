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
        if instancia.id_dbms in [2, 3]: # MySQL 5 u 8
            session_remota = get_dynamic_session(servidor, credencial, dbms_id=instancia.id_dbms)
            remote_dbs = get_mysql_remote_databases(session_remota)
        else:
            return {"error": f"DBMS ID {instancia.id_dbms} no soportado para auto-búsqueda actualmente"}
    except Exception as e:
        return {"error": f"Fallo en conexión remota: {str(e)}"}
    finally:
        if session_remota:
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
