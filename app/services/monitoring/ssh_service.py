from sqlalchemy.orm import Session
from app.models.monitoring_persistence_models import Monitoreo, Metrica, TipoMetrica
from app.models.infrastructure_models import Servidor, CredencialAcceso, InstanciaDBMS, BaseDeDatos, DBMS
from app.models.backup_models import RutaRespaldo, Respaldo, AsignacionPoliticaBD, PoliticaRespaldo
from app.models.audit_model import Bitacora
from app.core.ssh_orchestrator import get_ssh_connection
from datetime import datetime
from decimal import Decimal
from .ssh import metrics_provider, discovery_provider

def run_ssh_monitoring(db_local: Session, servidor_id: int, credencial_id: int):
    """
    ORQUESTADOR DE MONITOREO: Valida, Conecta, Ejecuta y Persiste.
    """
    servidor = db_local.query(Servidor).filter(Servidor.id_servidor == servidor_id).first()
    credencial = db_local.query(CredencialAcceso).filter(CredencialAcceso.id_credencial == credencial_id).first()

    if not servidor or not credencial:
        return {"error": "Servidor o Credencial no encontrados"}

    # Iniciar registro en Monitoreo
    nuevo_monitoreo = Monitoreo(
        id_servidor=servidor_id,
        id_credencial=credencial_id,
        id_estado_monitoreo=1 # Activo
    )
    db_local.add(nuevo_monitoreo)
    db_local.commit()
    db_local.refresh(nuevo_monitoreo)

    client = None
    try:
        # 1. CONECTAR
        client = get_ssh_connection(servidor, credencial)
        
        # 2. EJECUTAR (Selección de perfil según flag legacy)
        if servidor.es_legacy:
            raw_metrics = metrics_provider.get_metrics_legacy(client)
        else:
            raw_metrics = metrics_provider.get_metrics_modern(client)

        # 3. PERSISTIR
        for nombre, valor in raw_metrics.items():
            tipo = db_local.query(TipoMetrica).filter(TipoMetrica.nombre_tipo == nombre).first()
            if not tipo:
                tipo = TipoMetrica(nombre_tipo=nombre, unidad_medida="%" if "Usage" in nombre else "Días")
                db_local.add(tipo)
                db_local.commit()
                db_local.refresh(tipo)

            db_local.add(Metrica(
                valor=valor,
                id_monitoreo=nuevo_monitoreo.id_monitoreo,
                id_tipo_metrica=tipo.id_tipo_metrica
            ))

        nuevo_monitoreo.fecha_fin = datetime.now()
        nuevo_monitoreo.id_estado_monitoreo = 4 # Éxito según seed (antes 2)
        db_local.commit()

        return {
            "monitoreo_id": nuevo_monitoreo.id_monitoreo,
            "servidor": servidor.nombre_servidor,
            "legacy": servidor.es_legacy,
            "metrics": raw_metrics,
            "status": "success"
        }

    except Exception as e:
        nuevo_monitoreo.id_estado_monitoreo = 5 # Fallo según seed
        db_local.commit()
        raise e
    finally:
        if client:
            client.close()

def run_integrated_file_discovery(db: Session, instancia_id: int, credencial_id: int, ruta_id: int, user_id: int):
    """
    DESCUBRIMIENTO INTEGRADO: 
    Busca archivos, los asocia a BDs y registra en la tabla Respaldo.
    """
    # 1. Obtener Entidades
    instancia = db.query(InstanciaDBMS).filter(InstanciaDBMS.id_instancia == instancia_id).first()
    ruta = db.query(RutaRespaldo).filter(RutaRespaldo.id_ruta == ruta_id).first()
    credencial = db.query(CredencialAcceso).filter(CredencialAcceso.id_credencial == credencial_id).first()
    
    if not instancia or not ruta or not credencial:
        return {"error": "Instancia, Ruta o Credencial no encontrados"}

    servidor = instancia.servidor
    dbms = db.query(DBMS).filter(DBMS.id_dbms == instancia.id_dbms).first()
    
    # 2. Mapeo de Extensiones
    extension_map = {
        "PostgreSQL": ".sql",
        "MySQL": ".sql",
        "Oracle Database": ".dmp",
        "MongoDB": ".archive"
    }
    ext = extension_map.get(dbms.nombre_dbms, ".sql")

    # 3. Conexión SSH
    client = None
    try:
        client = get_ssh_connection(servidor, credencial)
        if servidor.es_legacy:
            found_files = discovery_provider.search_files_legacy(client, ruta.path, ext)
        else:
            found_files = discovery_provider.search_files_modern(client, ruta.path, ext)

        # 4. Procesar archivos y llenar tabla Respaldo
        databases = db.query(BaseDeDatos).filter(BaseDeDatos.id_instancia == instancia_id).all()
        respaldos_creados = 0

        for file_path, size_bytes in found_files:
            # Intentar asociar archivo a una BD por nombre
            for bd in databases:
                if bd.nombre_base.lower() in file_path.lower():
                    # Buscar política asociada a esta BD
                    asignacion = db.query(AsignacionPoliticaBD).filter(
                        AsignacionPoliticaBD.id_base_datos == bd.id_base_datos
                    ).first()
                    
                    if asignacion:
                        # Crear registro de respaldo
                        nuevo_respaldo = Respaldo(
                            id_base_datos=bd.id_base_datos,
                            id_politica=asignacion.id_politica,
                            id_credencial=credencial_id,
                            id_ruta_respaldo=ruta_id,
                            id_estado_ejecucion=4, # Éxito
                            tamano_mb=Decimal(str(round(size_bytes / (1024 * 1024), 2))),
                            fecha_fin=datetime.now()
                        )
                        db.add(nuevo_respaldo)
                        respaldos_creados += 1
                        break # Ya asociamos este archivo a una BD

        # 5. Auditoría
        nueva_bitacora = Bitacora(
            entidad_afectada="Respaldo",
            id_entidad=instancia_id, # Usamos ID instancia como referencia grupal
            descripcion_evento=f"Descubrimiento SSH en {ruta.path}. Archivos: {len(found_files)}, Registrados: {respaldos_creados}",
            id_usuario=user_id,
            id_tipo_evento=6 # Ejecución de Respaldo
        )
        db.add(nueva_bitacora)
        db.commit()

        return {
            "status": "success",
            "servidor": servidor.direccion_ip,
            "ruta": ruta.path,
            "archivos_fisicos": len(found_files),
            "registros_respaldo_creados": respaldos_creados
        }

    finally:
        if client:
            client.close()
