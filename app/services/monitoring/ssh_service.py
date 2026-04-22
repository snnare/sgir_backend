from sqlalchemy.orm import Session
from app.models.monitoring_persistence_models import Monitoreo, Metrica, TipoMetrica
from app.models.infrastructure_models import Servidor, CredencialAcceso
from app.core.ssh_orchestrator import get_ssh_connection
from datetime import datetime
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
        nuevo_monitoreo.id_estado_monitoreo = 2 # Completado
        db_local.commit()

        return {
            "monitoreo_id": nuevo_monitoreo.id_monitoreo,
            "servidor": servidor.nombre_servidor,
            "legacy": servidor.es_legacy,
            "metrics": raw_metrics,
            "status": "success"
        }

    except Exception as e:
        nuevo_monitoreo.id_estado_monitoreo = 3 # Fallido
        db_local.commit()
        raise e
    finally:
        if client:
            client.close()

def run_file_discovery(db_local: Session, servidor_id: int, credencial_id: int, path: str, extension: str):
    """
    ORQUESTADOR DE DESCUBRIMIENTO: Busca archivos en el servidor remoto.
    """
    servidor = db_local.query(Servidor).filter(Servidor.id_servidor == servidor_id).first()
    credencial = db_local.query(CredencialAcceso).filter(CredencialAcceso.id_credencial == credencial_id).first()

    if not servidor or not credencial:
        return {"error": "Servidor o Credencial no encontrados"}

    client = None
    try:
        client = get_ssh_connection(servidor, credencial)
        
        if servidor.es_legacy:
            files = discovery_provider.search_files_legacy(client, path, extension)
        else:
            files = discovery_provider.search_files_modern(client, path, extension)

        return {
            "servidor": servidor.nombre_servidor,
            "path_busqueda": path,
            "extension": extension,
            "archivos_encontrados": files,
            "total": len(files),
            "status": "success"
        }
    except Exception as e:
        raise e
    finally:
        if client:
            client.close()
