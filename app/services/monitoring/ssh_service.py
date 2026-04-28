from sqlalchemy.orm import Session
from app.models.monitoring_persistence_models import Monitoreo, Metrica, TipoMetrica, Alerta
from app.models.infrastructure_models import Servidor, CredencialAcceso, InstanciaDBMS, BaseDeDatos, DBMS
from app.models.backup_models import RutaRespaldo, Respaldo, AsignacionPoliticaBD, PoliticaRespaldo
from app.models.audit_model import Bitacora
from app.core.ssh_orchestrator import get_ssh_connection
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from .ssh import metrics_provider, discovery_provider

def run_ssh_monitoring(db_local: Session, servidor_id: int, credencial_id: int):
    """
    ORQUESTADOR DE MONITOREO CON UMBRAL (>= 90%):
    Registra la sesión siempre (latido), pero solo guarda métricas si superan el umbral.
    """
    servidor = db_local.query(Servidor).filter(Servidor.id_servidor == servidor_id).first()
    credencial = db_local.query(CredencialAcceso).filter(CredencialAcceso.id_credencial == credencial_id).first()

    if not servidor or not credencial:
        return {"error": "Servidor o Credencial no encontrados"}

    # Iniciar registro en Monitoreo (El "Latido" del sistema)
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
        
        # 2. EJECUTAR
        if servidor.es_legacy:
            raw_metrics = metrics_provider.get_metrics_legacy(client)
        else:
            raw_metrics = metrics_provider.get_metrics_modern(client)

        # 3. FILTRADO Y PERSISTENCIA (Solo >= 90%)
        exceso_detectado = False
        detalles_exceso = []

        for nombre, valor in raw_metrics.items():
            # Solo evaluamos CPU, RAM y Disco para el umbral
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

        # 4. GESTIÓN DE ALERTAS AUTOMÁTICAS
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
            "servidor": servidor.nombre_servidor,
            "alerta": exceso_detectado,
            "status": "success"
        }

    except Exception as e:
        nuevo_monitoreo.id_estado_monitoreo = 5 # Fallo
        db_local.commit()
        raise e
    finally:
        if client:
            client.close()

def get_server_health_status(db: Session, servidor_id: int):
    """
    SERVICIO PARA EL FRONTEND: Determina la salud del servidor sin sockets.
    Interpretación:
    - Sin sesión reciente (> 5 min): Desconocido (Gris)
    - Sesión con métricas: Crítico (Rojo)
    - Sesión sin métricas: Sano (Verde)
    """
    # 1. Buscar la última sesión de monitoreo exitosa
    last_session = db.query(Monitoreo).filter(
        Monitoreo.id_servidor == servidor_id,
        Monitoreo.id_estado_monitoreo == 4
    ).order_by(Monitoreo.id_monitoreo.desc()).first()

    if not last_session:
        return {"status": "unknown", "message": "No hay datos de monitoreo"}

    # 2. Validar frescura (Si la última vez fue hace más de 5 mins, algo anda mal con el scheduler)
    ahora = datetime.now(timezone.utc)
    # last_session.fecha_inicio ya tiene tzinfo si se configuró bien, si no, lo comparamos igual
    diferencia = ahora - last_session.fecha_inicio
    
    if diferencia > timedelta(minutes=5):
        return {
            "status": "stale", 
            "message": "Monitoreo desactualizado", 
            "last_check": last_session.fecha_inicio
        }

    # 3. Verificar si tiene métricas (si las tiene es porque superó el 90%)
    has_metrics = db.query(Metrica).filter(Metrica.id_monitoreo == last_session.id_monitoreo).first()
    
    if has_metrics:
        # Recuperar cuáles
        metrics = db.query(Metrica, TipoMetrica).join(TipoMetrica).filter(
            Metrica.id_monitoreo == last_session.id_monitoreo
        ).all()
        return {
            "status": "critical",
            "message": "Recursos excedidos (>= 90%)",
            "details": [{"tipo": t.nombre_tipo, "valor": float(m.valor)} for m, t in metrics],
            "last_check": last_session.fecha_inicio
        }

    return {
        "status": "healthy",
        "message": "Recursos en niveles normales (< 90%)",
        "last_check": last_session.fecha_inicio
    }

def run_integrated_file_discovery(db: Session, instancia_id: int, credencial_id: int, ruta_id: int, user_id: int):
    # ... (Mantenemos la lógica de descubrimiento sin cambios)
    # (Copio el resto del archivo para que no se pierda nada)
    instancia = db.query(InstanciaDBMS).filter(InstanciaDBMS.id_instancia == instancia_id).first()
    ruta = db.query(RutaRespaldo).filter(RutaRespaldo.id_ruta == ruta_id).first()
    credencial = db.query(CredencialAcceso).filter(CredencialAcceso.id_credencial == credencial_id).first()
    
    if not instancia or not ruta or not credencial:
        return {"error": "Instancia, Ruta o Credencial no encontrados"}

    servidor = instancia.servidor
    dbms = db.query(DBMS).filter(DBMS.id_dbms == instancia.id_dbms).first()
    
    extension_map = {"PostgreSQL": ".sql", "MySQL": ".sql", "Oracle Database": ".dmp", "MongoDB": ".archive"}
    ext = extension_map.get(dbms.nombre_dbms, ".sql")

    client = None
    try:
        client = get_ssh_connection(servidor, credencial)
        if servidor.es_legacy:
            found_files = discovery_provider.search_files_legacy(client, ruta.path, ext)
        else:
            found_files = discovery_provider.search_files_modern(client, ruta.path, ext)

        databases = db.query(BaseDeDatos).filter(BaseDeDatos.id_instancia == instancia_id).all()
        respaldos_creados = 0

        for file_path, size_bytes in found_files:
            for bd in databases:
                if bd.nombre_base.lower() in file_path.lower():
                    asignacion = db.query(AsignacionPoliticaBD).filter(AsignacionPoliticaBD.id_base_datos == bd.id_base_datos).first()
                    if asignacion:
                        nuevo_respaldo = Respaldo(
                            id_base_datos=bd.id_base_datos, id_politica=asignacion.id_politica,
                            id_credencial=credencial_id, id_ruta_respaldo=ruta_id,
                            id_estado_ejecucion=4, tamano_mb=Decimal(str(round(size_bytes / (1024 * 1024), 2))),
                            fecha_fin=datetime.now()
                        )
                        db.add(nuevo_respaldo)
                        respaldos_creados += 1
                        break

        nueva_bitacora = Bitacora(
            entidad_afectada="Respaldo", id_entidad=instancia_id,
            descripcion_evento=f"Descubrimiento SSH en {ruta.path}. Archivos: {len(found_files)}, Registrados: {respaldos_creados}",
            id_usuario=user_id, id_tipo_evento=6
        )
        db.add(nueva_bitacora)
        db.commit()
        return {"status": "success", "servidor": servidor.direccion_ip, "ruta": ruta.path, "archivos_fisicos": len(found_files), "registros_respaldo_creados": respaldos_creados}
    finally:
        if client: client.close()
