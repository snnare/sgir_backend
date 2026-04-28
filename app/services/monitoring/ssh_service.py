from sqlalchemy.orm import Session
from app.models.monitoring_persistence_models import Monitoreo, Metrica, TipoMetrica, Alerta
from app.models.infrastructure_models import Servidor, CredencialAcceso, InstanciaDBMS, BaseDeDatos, DBMS
from app.models.backup_models import RutaRespaldo, Respaldo, AsignacionPoliticaBD, PoliticaRespaldo
from app.models.audit_model import Bitacora
from app.core.ssh_orchestrator import get_ssh_connection
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from .ssh import metrics_provider, discovery_provider

# CACHÉ GLOBAL EN MEMORIA: Almacena el último latido de cada servidor
# Estructura: { servidor_id: {"cpu": 10.5, "ram": 45.2, "disk": 30.0, "last_update": datetime} }
LIVE_METRICS_CACHE = {}

def run_ssh_monitoring(db_local: Session, servidor_id: int, credencial_id: int):
    """
    MONITOREO CON LIVE CACHE Y UMBRAL (90%):
    Actualiza siempre la memoria para el front, pero solo persiste en DB si hay alarma.
    """
    servidor = db_local.query(Servidor).filter(Servidor.id_servidor == servidor_id).first()
    credencial = db_local.query(CredencialAcceso).filter(CredencialAcceso.id_credencial == credencial_id).first()

    if not servidor or not credencial:
        return {"error": "Servidor o Credencial no encontrados"}

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
        client = get_ssh_connection(servidor, credencial)
        
        if servidor.es_legacy:
            raw_metrics = metrics_provider.get_metrics_legacy(client)
        else:
            raw_metrics = metrics_provider.get_metrics_modern(client)

        # 1. ACTUALIZAR LIVE CACHE (Siempre, para las Cards del Front)
        LIVE_METRICS_CACHE[servidor_id] = {
            "cpu": float(raw_metrics.get("CPU_Usage", 0)),
            "ram": float(raw_metrics.get("RAM_Usage", 0)),
            "disk": float(raw_metrics.get("Disk_Usage", 0)),
            "uptime": float(raw_metrics.get("Uptime", 0)),
            "last_update": datetime.now(timezone.utc)
        }

        # 2. FILTRADO POR UMBRAL (Solo >= 90% va a la tabla 'metrica')
        exceso_detectado = False
        detalles_exceso = []

        for nombre, valor in raw_metrics.items():
            if any(key in nombre for key in ["CPU", "RAM", "Disk"]):
                if valor >= 90:
                    exceso_detectado = True
                    detalles_exceso.append(f"{nombre}: {valor}%")
                    
                    tipo = db_local.query(TipoMetrica).filter(TipoMetrica.nombre_tipo == nombre).first()
                    if not tipo:
                        tipo = TipoMetrica(nombre_tipo=nombre, unidad_medida="%")
                        db_local.add(tipo)
                        db_local.commit()
                        db_local.refresh(tipo)

                    db_local.add(Metrica(
                        valor=valor,
                        id_monitoreo=nuevo_monitoreo.id_monitoreo,
                        id_tipo_metrica=tipo.id_tipo_metrica
                    ))

        # 3. ALERTAS EN DB
        if exceso_detectado:
            nueva_alerta = Alerta(
                descripcion=f"Umbral superado en {servidor.nombre_servidor}: {', '.join(detalles_exceso)}",
                id_servidor=servidor_id,
                id_monitoreo=nuevo_monitoreo.id_monitoreo,
                id_nivel_alerta=3, # Crítico
                id_estado_alerta=6 # Abierta
            )
            db_local.add(nueva_alerta)

        nuevo_monitoreo.fecha_fin = datetime.now()
        nuevo_monitoreo.id_estado_monitoreo = 4 # Éxito
        db_local.commit()

        return {
            "monitoreo_id": nuevo_monitoreo.id_monitoreo,
            "alerta": exceso_detectado,
            "live_data": LIVE_METRICS_CACHE[servidor_id]
        }

    except Exception as e:
        nuevo_monitoreo.id_estado_monitoreo = 5 # Fallo
        db_local.commit()
        raise e
    finally:
        if client: client.close()

def get_server_health_status(db: Session, servidor_id: int):
    """
    SERVICIO PARA EL FRONTEND: Combina estado de salud con métricas en tiempo real (Cache).
    """
    # 1. Obtener datos en vivo desde el caché de memoria
    live_data = LIVE_METRICS_CACHE.get(servidor_id)
    
    # 2. Consultar última sesión en DB para el status general
    last_session = db.query(Monitoreo).filter(
        Monitoreo.id_servidor == servidor_id,
        Monitoreo.id_estado_monitoreo == 4
    ).order_by(Monitoreo.id_monitoreo.desc()).first()

    if not last_session:
        return {"status": "unknown", "message": "Esperando primer ciclo de monitoreo..."}

    # 3. Calcular frescura
    ahora = datetime.now(timezone.utc)
    diferencia = ahora - last_session.fecha_inicio
    is_stale = diferencia > timedelta(minutes=5)

    # 4. Determinar Status basado en alertas (si hubo métricas >= 90)
    has_incident = db.query(Metrica).filter(Metrica.id_monitoreo == last_session.id_monitoreo).first()
    
    status = "healthy"
    if is_stale: status = "stale"
    elif has_incident: status = "critical"

    return {
        "status": status,
        "last_check": last_session.fecha_inicio,
        "is_stale": is_stale,
        "live_metrics": live_data if live_data else {
            "cpu": 0, "ram": 0, "disk": 0, "uptime": 0, "message": "Datos de caché no disponibles"
        }
    }

def run_integrated_file_discovery(db: Session, instancia_id: int, credencial_id: int, ruta_id: int, user_id: int):
    instancia = db.query(InstanciaDBMS).filter(InstanciaDBMS.id_instancia == instancia_id).first()
    ruta = db.query(RutaRespaldo).filter(RutaRespaldo.id_ruta == ruta_id).first()
    credencial = db.query(CredencialAcceso).filter(CredencialAcceso.id_credencial == credencial_id).first()
    if not instancia or not ruta or not credencial: return {"error": "Instancia, Ruta o Credencial no encontrados"}
    servidor = instancia.servidor
    dbms = db.query(DBMS).filter(DBMS.id_dbms == instancia.id_dbms).first()
    extension_map = {"PostgreSQL": ".sql", "MySQL": ".sql", "Oracle Database": ".dmp", "MongoDB": ".archive"}
    ext = extension_map.get(dbms.nombre_dbms, ".sql")
    client = None
    try:
        client = get_ssh_connection(servidor, credencial)
        found_files = discovery_provider.search_files_legacy(client, ruta.path, ext) if servidor.es_legacy else discovery_provider.search_files_modern(client, ruta.path, ext)
        databases = db.query(BaseDeDatos).filter(BaseDeDatos.id_instancia == instancia_id).all()
        respaldos_creados = 0
        for file_path, size_bytes in found_files:
            for bd in databases:
                if bd.nombre_base.lower() in file_path.lower():
                    asignacion = db.query(AsignacionPoliticaBD).filter(AsignacionPoliticaBD.id_base_datos == bd.id_base_datos).first()
                    if asignacion:
                        nuevo_respaldo = Respaldo(id_base_datos=bd.id_base_datos, id_politica=asignacion.id_politica, id_credencial=credencial_id, id_ruta_respaldo=ruta_id, id_estado_ejecucion=4, tamano_mb=Decimal(str(round(size_bytes / (1024 * 1024), 2))), fecha_fin=datetime.now())
                        db.add(nuevo_respaldo)
                        respaldos_creados += 1
                        break
        nueva_bitacora = Bitacora(entidad_afectada="Respaldo", id_entidad=instancia_id, descripcion_evento=f"Descubrimiento SSH en {ruta.path}. Archivos: {len(found_files)}, Registrados: {respaldos_creados}", id_usuario=user_id, id_tipo_evento=6)
        db.add(nueva_bitacora)
        db.commit()
        return {"status": "success", "servidor": servidor.direccion_ip, "ruta": ruta.path, "archivos_fisicos": len(found_files), "registros_respaldo_creados": respaldos_creados}
    finally:
        if client: client.close()
