from sqlalchemy.orm import Session
from app.models.infrastructure_models import BaseDeDatos, InstanciaDBMS
from app.core.dynamic_db_core import get_dynamic_session
from app.services.monitoring.mysql5.mysql5_service import list_databases_discovery as list_mysql_dbs
from app.services.monitoring.mongodb.mongodb_service import list_databases_discovery as list_mongo_dbs
from app.services.infrastructure_crud import get_instancia, get_servidor, get_credencial

def sync_databases_inventory(db: Session, instancia_id: int):
    """
    Sincroniza la realidad del servidor con la tabla Base_de_Datos local.
    """
    instancia = get_instancia(db, instancia_id)
    if not instancia:
        return {"error": "Instancia no encontrada"}
    
    servidor = get_servidor(db, instancia.id_servidor)
    # Buscamos una credencial tipo DB (ID 2 en seed) para este servidor
    # Idealmente, el flujo debería recibir la credencial_id específica.
    # Por ahora tomamos la primera disponible para simplificar el flujo ad-hoc.
    from app.models.infrastructure_models import CredencialAcceso
    credencial = db.query(CredencialAcceso).filter(
        CredencialAcceso.id_servidor == servidor.id_servidor,
        CredencialAcceso.id_tipo_acceso == 2 # DB Native
    ).first()

    if not credencial:
        return {"error": "No se encontró credencial de base de datos para esta instancia"}

    # 1. Obtener lista remota
    remote_dbs = []
    if instancia.id_dbms in [2, 3]: # MySQL 5 u 8
        remote_conn = get_dynamic_session(servidor, credencial, dbms_id=instancia.id_dbms)
        remote_dbs = list_mysql_dbs(remote_conn)
        remote_conn.close()
    elif instancia.id_dbms == 5: # MongoDB
        client = get_dynamic_session(servidor, credencial, dbms_id=5)
        remote_dbs = list_mongo_dbs(client)
        client.close()

    # 2. Sincronizar localmente (Upsert)
    sync_results = {"created": 0, "updated": 0, "deactivated": 0}
    remote_names = [d["nombre"] for d in remote_dbs]

    # Desactivar dbs que ya no existen en el remoto
    local_dbs = db.query(BaseDeDatos).filter(BaseDeDatos.id_instancia == instancia_id).all()
    for l_db in local_dbs:
        if l_db.nombre_base not in remote_names:
            l_db.id_estado_bd = 2 # Inactivo (basado en seed)
            sync_results["deactivated"] += 1

    # Insertar o actualizar dbs remotas
    for r_db in remote_dbs:
        db_exists = db.query(BaseDeDatos).filter(
            BaseDeDatos.id_instancia == instancia_id,
            BaseDeDatos.nombre_base == r_db["nombre"]
        ).first()

        if db_exists:
            db_exists.tamano_mb = r_db["tamano_mb"]
            db_exists.id_estado_bd = 1 # Activo
            sync_results["updated"] += 1
        else:
            new_entry = BaseDeDatos(
                nombre_base=r_db["nombre"],
                tamano_mb=r_db["tamano_mb"],
                id_instancia=instancia_id,
                id_estado_bd=1
            )
            db.add(new_entry)
            sync_results["created"] += 1

    db.commit()
    return sync_results
