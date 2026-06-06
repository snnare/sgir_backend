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

def run_ssh_monitoring(db_local: Session, servidor_id: int, credencial_id: int, use_pool: bool = True):
    """
    MONITOREO CON LIVE CACHE, POOLING Y UMBRAL (90%):
    Reutiliza conexiones del Pool para evitar sobrecarga de red.
    """
    servidor = db_local.query(Servidor).filter(Servidor.id_servidor == servidor_id).first()
    credencial = db_local.query(CredencialAcceso).filter(CredencialAcceso.id_credencial == credencial_id).first()

    if not servidor or not credencial:
        return {"error": "Servidor o Credencial no encontrados"}

    nuevo_monitoreo = Monitoreo(
        id_servidor=servidor_id,
        id_estado_monitoreo=1 # Activo
    )
    db_local.add(nuevo_monitoreo)
    db_local.commit()
    db_local.refresh(nuevo_monitoreo)

    client = None
    try:
        # Usar el Pool para el monitoreo recurrente
        client = get_ssh_connection(servidor, credencial, use_pool=use_pool)
        
        # Obtener particiones configuradas
        partition_paths = [p.path for p in servidor.particiones] if servidor.particiones else ["/"]

        if servidor.es_legacy:
            raw_metrics = metrics_provider.get_metrics_legacy(client, partition_paths)
        else:
            raw_metrics = metrics_provider.get_metrics_modern(client, partition_paths)

        # 1. ACTUALIZAR LIVE CACHE COMPACTO (Ahorro de bytes)
        # Formato: "cpu|ram|disco1:val,disco2:val|uptime|timestamp"
        cpu = round(float(raw_metrics.get("CPU_Usage", 0)), 1)
        ram = round(float(raw_metrics.get("RAM_Usage", 0)), 1)
        uptime = round(float(raw_metrics.get("Uptime", 0)), 1)
        
        disks_str = ",".join([
            f"{k.split('(')[1].split(')')[0]}:{round(float(v), 1)}" 
            for k, v in raw_metrics.items() if "Disk_Usage" in k
        ])
        
        timestamp = int(datetime.now(timezone.utc).timestamp())
        
        LIVE_METRICS_CACHE[servidor_id] = f"{cpu}|{ram}|{disks_str}|{uptime}|{timestamp}"

        # 2. FILTRADO POR UMBRAL (Diferenciado por recurso y con alertas inteligentes)
        # CPU >= 90%, RAM >= 85%, Disk >= 80% (Warning) / >= 90% (Critical)
        exceso_detectado = False
        detalles_exceso = []

        for nombre, valor in raw_metrics.items():
            excede_umbral = False
            nivel_alerta_sugerido = 3 # Por defecto Crítico

            if "CPU" in nombre and valor >= 90:
                excede_umbral = True
                nivel_alerta_sugerido = 3
                detalles_exceso.append(f"{nombre}: {valor}% (Crítico)")
            elif "RAM" in nombre and valor >= 85:
                excede_umbral = True
                # Si está entre 85 y 91 es Advertencia, >= 92 es Crítico
                nivel_alerta_sugerido = 2 if valor < 92 else 3
                nivel_str = "Advertencia" if nivel_alerta_sugerido == 2 else "Crítico"
                detalles_exceso.append(f"{nombre}: {valor}% ({nivel_str})")
            elif "Disk" in nombre and valor >= 80:
                excede_umbral = True
                # Almacenamiento: >= 80% es Warning, >= 90% es Crítico
                nivel_alerta_sugerido = 2 if valor < 90 else 3
                nivel_str = "Advertencia" if nivel_alerta_sugerido == 2 else "Crítico"
                
                # Extraer punto de montaje de la métrica (ej: "Disk_Usage_(/)" -> "/")
                partition_name = nombre
                if "(" in nombre and ")" in nombre:
                    try:
                        partition_name = nombre.split("(")[1].split(")")[0]
                    except Exception:
                        pass
                
                # Control de spam: Verificar si ya existe una alerta ABIERTA (id_estado_alerta=6) para esta partición
                existing_disk_alert = db_local.query(Alerta).filter(
                    Alerta.id_servidor == servidor_id,
                    Alerta.id_estado_alerta == 6,
                    Alerta.descripcion.like(f"%partición {partition_name}%")
                ).first()

                if not existing_disk_alert:
                    # Crear alerta de almacenamiento específica e independiente
                    desc_alerta = (
                        f"¡ALERTA!: Almacenamiento en la partición {partition_name} superó el umbral "
                        f"con {valor}% ({nivel_str}) en el servidor {servidor.nombre_servidor}."
                    )
                    nueva_alerta_disco = Alerta(
                        descripcion=desc_alerta,
                        id_servidor=servidor_id,
                        id_monitoreo=nuevo_monitoreo.id_monitoreo,
                        id_nivel_alerta=nivel_alerta_sugerido,
                        id_estado_alerta=6 # Abierta
                    )
                    db_local.add(nueva_alerta_disco)

            if excede_umbral:
                # Guardar en base de datos si supera el umbral del recurso
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
                
                # Si no es Disk, lo agregamos para la alerta agrupada de hardware (CPU/RAM)
                if "Disk" not in nombre:
                    exceso_detectado = True

        # 3. ALERTAS DE HARDWARE GENERAL EN DB (Para CPU/RAM)
        if exceso_detectado:
            # Comprobar si ya existe una alerta general abierta de hardware para no duplicar
            existing_hw_alert = db_local.query(Alerta).filter(
                Alerta.id_servidor == servidor_id,
                Alerta.id_estado_alerta == 6,
                Alerta.descripcion.like("Umbral de hardware superado%")
            ).first()

            if not existing_hw_alert:
                nueva_alerta = Alerta(
                    descripcion=f"Umbral de hardware superado en {servidor.nombre_servidor}: {', '.join(detalles_exceso)}",
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
        # IMPORTANTE: NO cerrar el cliente si viene del pool
        if not use_pool and client:
            client.close()

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

    # Decodificar cache compacto si existe para la respuesta individual
    decoded_metrics = {
        "cpu": 0, "ram": 0, "disks": {}, "uptime": 0, "message": "Datos de caché no disponibles"
    }
    
    if live_data and isinstance(live_data, str):
        try:
            parts = live_data.split("|")
            decoded_metrics = {
                "cpu": float(parts[0]),
                "ram": float(parts[1]),
                "disks": {d.split(":")[0]: float(d.split(":")[1]) for d in parts[2].split(",")} if parts[2] else {},
                "uptime": float(parts[3]),
                "timestamp": int(parts[4])
            }
        except Exception:
            pass

    return {
        "status": status,
        "last_check": last_session.fecha_inicio,
        "is_stale": is_stale,
        "live_metrics": decoded_metrics
    }

def get_global_health_summary(db: Session):
    """
    RESUMEN GLOBAL: Devuelve conteos de estados para el Dashboard principal.
    """
    total_servers = db.query(Servidor).filter(Servidor.id_estado_servidor == 1).count()
    
    # 1. Obtener todas las sesiones de monitoreo más recientes por servidor
    # (Unificamos lógica para determinar cuántos están en cada estado)
    from sqlalchemy import func
    subquery = db.query(
        Monitoreo.id_servidor,
        func.max(Monitoreo.fecha_inicio).label("max_date")
    ).filter(Monitoreo.id_estado_monitoreo == 4).group_by(Monitoreo.id_servidor).subquery()

    recent_sessions = db.query(Monitoreo).join(
        subquery, (Monitoreo.id_servidor == subquery.c.id_servidor) & (Monitoreo.fecha_inicio == subquery.c.max_date)
    ).all()

    summary = {
        "total_active_servers": total_servers,
        "healthy": 0,
        "critical": 0,
        "stale": 0,
        "unknown": total_servers - len(recent_sessions)
    }

    ahora = datetime.now(timezone.utc)
    for session in recent_sessions:
        # Frescura
        if ahora - session.fecha_inicio > timedelta(minutes=10):
            summary["stale"] += 1
            continue
        
        # Incidentes (Métricas >= 90)
        has_incident = db.query(Metrica).filter(Metrica.id_monitoreo == session.id_monitoreo).first()
        if has_incident:
            summary["critical"] += 1
        else:
            summary["healthy"] += 1

    return summary

def run_integrated_file_discovery(db: Session, instancia_id: int, credencial_id: int, ruta_id: int, user_id: int):
    instancia = db.query(InstanciaDBMS).filter(InstanciaDBMS.id_instancia == instancia_id).first()
    ruta = db.query(RutaRespaldo).filter(RutaRespaldo.id_ruta == ruta_id).first()
    credencial = db.query(CredencialAcceso).filter(CredencialAcceso.id_credencial == credencial_id).first()
    if not instancia or not ruta or not credencial: return {"error": "Instancia, Ruta o Credencial no encontrados"}
    servidor = instancia.servidor

    # Validación de pertenencia de ruta
    if ruta.id_servidor != servidor.id_servidor:
        return {"error": f"La ruta {ruta.path} no pertenece al servidor {servidor.nombre_servidor}"}

    dbms = db.query(DBMS).filter(DBMS.id_dbms == instancia.id_dbms).first()
    # Mapeo de extensiones por motor (RDBMS) incluyendo formatos comprimidos/empaquetados
    extension_map = {
        "PostgreSQL": [".sql", ".sql.gz", ".tar", ".zip", ".gz"],
        "MySQL": [".sql", ".sql.gz", ".tar", ".zip", ".gz"],
        "Oracle Database": [".dmp", ".dmp.gz", ".tar", ".zip", ".gz"],
        "MongoDB": [".archive", ".tar.gz", ".tar", ".zip", ".gz"]
    }
    exts = extension_map.get(dbms.nombre_dbms, [".sql"])
    client = None
    try:
        # Discovery suele ser una tarea puntual, pero podemos usar el pool si el servidor ya está bajo monitoreo
        client = get_ssh_connection(servidor, credencial, use_pool=True)
        
        found_files_list = []
        for ext in exts:
            files = discovery_provider.search_files_legacy(client, ruta.path, ext) if servidor.es_legacy else discovery_provider.search_files_modern(client, ruta.path, ext)
            found_files_list.extend(files)
            
        # Deduplicar archivos encontrados por su ruta física
        seen_paths = set()
        found_files = []
        for f in found_files_list:
            if f["path"] not in seen_paths:
                seen_paths.add(f["path"])
                found_files.append(f)
        databases = db.query(BaseDeDatos).filter(BaseDeDatos.id_instancia == instancia_id).all()
        respaldos_creados = 0
        detalles_response = []

        matched_paths = set()
        for bd in databases:
            matching_files = [f for f in found_files if bd.nombre_base.lower() in f["path"].lower()]
            
            asignacion = db.query(AsignacionPoliticaBD).filter(AsignacionPoliticaBD.id_base_datos == bd.id_base_datos).first()
            politica_nombre = "Sin política"
            id_politica = None
            if asignacion:
                politica = db.query(PoliticaRespaldo).filter(PoliticaRespaldo.id_politica == asignacion.id_politica).first()
                if politica:
                    politica_nombre = politica.nombre_politica
                    id_politica = politica.id_politica
            
            if matching_files:
                for f in matching_files:
                    matched_paths.add(f["path"])
                    file_path = f["path"]
                    size_bytes = f["size"]
                    file_name = file_path.split('/')[-1]
                    tamano_mb = round(size_bytes / (1024 * 1024), 2)
                    
                    if asignacion:
                        nuevo_respaldo = Respaldo(
                            id_base_datos=bd.id_base_datos,
                            id_politica=id_politica,
                            id_credencial=credencial_id,
                            id_estado_ejecucion=4,
                            nombre_archivo=file_name,
                            tamano_mb=Decimal(str(tamano_mb)),
                            path_fisico_origen=file_path,
                            ubicacion_actual="Origen",
                            ip_almacenado_actual=servidor.direccion_ip,
                            path_fisico_actual=file_path,
                            fecha_fin=datetime.now()
                        )
                        db.add(nuevo_respaldo)
                        respaldos_creados += 1
                    
                    detalles_response.append({
                        "base_datos_id": bd.id_base_datos,
                        "nombre_base": bd.nombre_base,
                        "politica_nombre": politica_nombre,
                        "ruta_path": file_path,
                        "archivo_encontrado": True,
                        "tamano_encontrado_mb": tamano_mb
                    })
            else:
                detalles_response.append({
                    "base_datos_id": bd.id_base_datos,
                    "nombre_base": bd.nombre_base,
                    "politica_nombre": politica_nombre,
                    "ruta_path": None,
                    "archivo_encontrado": False,
                    "tamano_encontrado_mb": 0.0
                })

        # Agregar archivos huérfanos/no registrados
        orphan_files = [f for f in found_files if f["path"] not in matched_paths]
        for f in orphan_files:
            file_path = f["path"]
            size_bytes = f["size"]
            file_name = file_path.split('/')[-1]
            tamano_mb = round(size_bytes / (1024 * 1024), 2)
            detalles_response.append({
                "base_datos_id": 0,
                "nombre_base": f"Desconocida ({file_name})",
                "politica_nombre": "Sin política",
                "ruta_path": file_path,
                "archivo_encontrado": True,
                "tamano_encontrado_mb": tamano_mb
            })

        nueva_bitacora = Bitacora(entidad_afectada="Respaldo", id_entidad=instancia_id, descripcion_evento=f"Descubrimiento SSH en {ruta.path}. Archivos: {len(found_files)}, Registrados: {respaldos_creados}", id_usuario=user_id, id_tipo_evento=6)
        db.add(nueva_bitacora)
        db.commit()

        return {
            "instancia_id": instancia_id,
            "ruta_escaneada": ruta.path,
            "archivos_procesados": len(found_files),
            "nuevos_respaldos_registrados": respaldos_creados,
            "detalles": detalles_response
        }
    finally:
        # No cerramos si viene del pool
        pass

def run_server_integrated_file_discovery(db: Session, servidor_id: int, credencial_id: int, ruta_id: int, user_id: int, days: int = 1, deep: bool = False):
    """
    Descubrimiento GLOBAL por servidor: Escanea backups de todas las instancias del servidor
    y retorna la verificación detallada de cada base de datos registrada.
    """
    servidor = db.query(Servidor).filter(Servidor.id_servidor == servidor_id).first()
    ruta = db.query(RutaRespaldo).filter(RutaRespaldo.id_ruta == ruta_id).first()
    credencial = db.query(CredencialAcceso).filter(CredencialAcceso.id_credencial == credencial_id).first()
    
    if not servidor or not ruta or not credencial: 
        return {"error": "Servidor, Ruta o Credencial no encontrados"}
    
    # Validación de pertenencia de ruta
    if ruta.id_servidor != servidor.id_servidor:
        return {"error": f"La ruta {ruta.path} no pertenece al servidor {servidor.nombre_servidor}"}

    client = None
    try:
        client = get_ssh_connection(servidor, credencial, use_pool=True)
        
        # Obtener archivos según antigüedad y profundidad
        if servidor.es_legacy:
            found_files = discovery_provider.list_recent_files_legacy(client, ruta.path, days=days, deep=deep)
        else:
            found_files = discovery_provider.list_recent_files_modern(client, ruta.path, days=days, deep=deep)

        # Buscar todas las instancias de este servidor
        from app.models.infrastructure_models import InstanciaDBMS, BaseDeDatos
        instances = db.query(InstanciaDBMS).filter(InstanciaDBMS.id_servidor == servidor_id).all()
        instance_ids = [inst.id_instancia for inst in instances]
        
        # Buscar todas las bases de datos de estas instancias
        databases = db.query(BaseDeDatos).filter(BaseDeDatos.id_instancia.in_(instance_ids)).all() if instance_ids else []

        results = []
        matched_names = set()
        respaldos_creados = 0
        for bd in databases:
            # Buscar archivos de respaldo coincidentes
            matching_files = [f for f in found_files if bd.nombre_base.lower() in f["name"].lower()]
            
            # Obtener política
            asignacion = db.query(AsignacionPoliticaBD).filter(AsignacionPoliticaBD.id_base_datos == bd.id_base_datos).first()
            politica_nombre = "Sin política"
            id_politica = None
            if asignacion:
                politica = db.query(PoliticaRespaldo).filter(PoliticaRespaldo.id_politica == asignacion.id_politica).first()
                if politica:
                    politica_nombre = politica.nombre_politica
                    id_politica = politica.id_politica

            if matching_files:
                for f in matching_files:
                    matched_names.add(f["name"])
                    file_path = f.get("path") or f"{ruta.path}/{f['name']}"
                    size_mb = round(f["size"] / (1024 * 1024), 2)
                    
                    if asignacion and id_politica:
                        # Evitar duplicados
                        existe = db.query(Respaldo).filter(
                            Respaldo.id_base_datos == bd.id_base_datos,
                            Respaldo.nombre_archivo == f["name"],
                            Respaldo.path_fisico_actual == file_path
                        ).first()
                        if not existe:
                            nuevo_respaldo = Respaldo(
                                id_base_datos=bd.id_base_datos,
                                id_politica=id_politica,
                                id_credencial=credencial_id,
                                id_estado_ejecucion=4, # 4: Ejecutado/Exitoso
                                nombre_archivo=f["name"],
                                tamano_mb=Decimal(str(size_mb)),
                                path_fisico_origen=file_path,
                                ubicacion_actual="Origen",
                                ip_almacenado_actual=servidor.direccion_ip,
                                path_fisico_actual=file_path,
                                fecha_fin=datetime.now()
                            )
                            db.add(nuevo_respaldo)
                            respaldos_creados += 1

                    results.append({
                        "base_datos_id": bd.id_base_datos,
                        "nombre_base": bd.nombre_base,
                        "politica_nombre": politica_nombre,
                        "ruta_path": file_path,
                        "archivo_encontrado": True,
                        "tamano_encontrado_mb": size_mb,
                        "timestamp_verificacion": datetime.now().isoformat(),
                        "detalle": "Respaldo verificado con éxito"
                    })
            else:
                results.append({
                    "base_datos_id": bd.id_base_datos,
                    "nombre_base": bd.nombre_base,
                    "politica_nombre": politica_nombre,
                    "ruta_path": None,
                    "archivo_encontrado": False,
                    "tamano_encontrado_mb": 0.0,
                    "timestamp_verificacion": datetime.now().isoformat(),
                    "detalle": "No se encontró archivo de respaldo reciente"
                })

        # Agregar archivos huérfanos/no registrados
        orphan_files = [f for f in found_files if f["name"] not in matched_names]
        for f in orphan_files:
            file_path = f.get("path") or f"{ruta.path}/{f['name']}"
            size_mb = round(f["size"] / (1024 * 1024), 2)
            results.append({
                "base_datos_id": 0,
                "nombre_base": f"Desconocida ({f['name']})",
                "politica_nombre": "Sin política",
                "ruta_path": file_path,
                "archivo_encontrado": True,
                "tamano_encontrado_mb": size_mb,
                "timestamp_verificacion": datetime.now().isoformat(),
                "detalle": "Archivo físico encontrado, pero la base de datos no está en la CMDB"
            })

        # Auditoría
        nueva_bitacora = Bitacora(
            entidad_afectada="Respaldo (Server Check)", 
            id_entidad=servidor_id, 
            descripcion_evento=f"Verificación global de backups en {ruta.path}. Bases de datos: {len(databases)}, Encontradas: {sum(1 for r in results if r['archivo_encontrado'])}", 
            id_usuario=user_id, 
            id_tipo_evento=6
        )
        db.add(nueva_bitacora)
        db.commit()

        return results
    finally:
        pass

def run_filesystem_discovery(db: Session, servidor_id: int):
    """
    Descubre puntos de montaje reales en el servidor remoto vía SSH.
    """
    servidor = db.query(Servidor).filter(Servidor.id_servidor == servidor_id).first()
    if not servidor:
        return {"error": "Servidor no encontrado"}
    
    # Buscar credencial SSH activa
    credencial = db.query(CredencialAcceso).filter(
        CredencialAcceso.id_servidor == servidor_id,
        CredencialAcceso.id_tipo_acceso == 1,
        CredencialAcceso.id_estado_credencial == 1
    ).first()

    if not credencial:
        return {"error": "El servidor no cuenta con credenciales SSH activas"}

    client = None
    try:
        client = get_ssh_connection(servidor, credencial, use_pool=True)
        filesystems = discovery_provider.discover_filesystems(client)
        
        return {
            "id_server": servidor.id_servidor,
            "ip_server": servidor.direccion_ip,
            "legacy": servidor.es_legacy,
            "filesystems": filesystems
        }
    except Exception as e:
        return {"error": f"Fallo en descubrimiento SSH: {str(e)}"}

def run_cron_discovery(db: Session, servidor_id: int, credencial_id: int):
    """
    Descubre tareas en crontab y sugiere frecuencias para la creación de políticas.
    """
    servidor = db.query(Servidor).filter(Servidor.id_servidor == servidor_id).first()
    credencial = db.query(CredencialAcceso).filter(CredencialAcceso.id_credencial == credencial_id).first()

    if not servidor or not credencial:
        return {"error": "Servidor o Credencial no encontrados"}

    client = None
    try:
        client = get_ssh_connection(servidor, credencial, use_pool=True)
        cron_tasks = discovery_provider.discover_cron_tasks(client)
        
        sugerencias = []
        for task in cron_tasks:
            sched = task["schedule"]
            freq_sugerida = 24 # Default diario
            
            # Lógica simple de sugerencia de frecuencia
            if sched == "@hourly": freq_sugerida = 1
            elif sched == "@daily": freq_sugerida = 24
            elif sched == "@weekly": freq_sugerida = 168
            elif "*/" in sched: # Ej: */2 * * * * (cada 2 min) o 0 */4 * * * (cada 4 horas)
                parts = sched.split()
                if "*/" in parts[1]: # Horas
                    try: freq_sugerida = int(parts[1].split("/")[1])
                    except: pass
                elif "*/" in parts[0]: # Minutos
                    # Si es cada X minutos, la frecuencia en horas es < 1, pero el modelo pide INT
                    # Sugerimos 1 hora como mínimo o lo que más se acerque
                    freq_sugerida = 1

            sugerencias.append({
                "linea_original": task["linea_completa"],
                "schedule": sched,
                "comando": task["command"],
                "frecuencia_sugerida_horas": freq_sugerida,
                "nombre_sugerido": f"Política: {task['command'].split('/')[-1]}"
            })
            
        return {
            "servidor": servidor.nombre_servidor,
            "ip": servidor.direccion_ip,
            "tareas_encontradas": len(sugerencias),
            "sugerencias": sugerencias
        }
    except Exception as e:
        return {"error": f"Error en descubrimiento de cron: {str(e)}"}


def run_bulk_backups_discovery(db: Session, user_id: int):
    """
    Auto-descubrimiento masivo de respaldos físicos.
    Busca todas las rutas de respaldo registradas y realiza el escaneo
    por cada servidor e instancia DBMS vinculada, registrando de forma inteligente
    las ejecuciones encontradas.
    """
    rutas = db.query(RutaRespaldo).all()
    
    summary = {
        "total_rutas_procesadas": 0,
        "total_respaldos_registrados": 0,
        "servidores_escaneados": [],
        "errores": []
    }
    
    # Tracking de servidores procesados por IP para el resumen
    processed_servers = set()
    
    for ruta in rutas:
        servidor = db.query(Servidor).filter(Servidor.id_servidor == ruta.id_servidor).first()
        if not servidor:
            continue
            
        # 1. Obtener la credencial SSH activa del servidor
        credencial = db.query(CredencialAcceso).filter(
            CredencialAcceso.id_servidor == servidor.id_servidor,
            CredencialAcceso.id_tipo_acceso == 1,  # Acceso SSH
            CredencialAcceso.id_estado_credencial == 1  # Activa
        ).first()
        
        if not credencial:
            summary["errores"].append({
                "servidor": servidor.nombre_servidor,
                "ruta": ruta.path,
                "error": "No cuenta con credenciales SSH activas"
            })
            continue
            
        # 2. Buscar todas las instancias registradas en este servidor
        instancias = db.query(InstanciaDBMS).filter(InstanciaDBMS.id_servidor == servidor.id_servidor).all()
        if not instancias:
            summary["errores"].append({
                "servidor": servidor.nombre_servidor,
                "ruta": ruta.path,
                "error": "No se encontraron instancias DBMS registradas"
            })
            continue
            
        summary["total_rutas_procesadas"] += 1
        if servidor.direccion_ip not in processed_servers:
            processed_servers.add(servidor.direccion_ip)
            summary["servidores_escaneados"].append(servidor.direccion_ip)
            
        # 3. Ejecutar el descubrimiento por cada instancia
        for instancia in instancias:
            try:
                # Reutiliza la lógica de descubrimiento por instancia
                res = run_integrated_file_discovery(db, instancia.id_instancia, credencial.id_credencial, ruta.id_ruta, user_id)
                if isinstance(res, dict) and "error" in res:
                    summary["errores"].append({
                        "servidor": servidor.nombre_servidor,
                        "instancia": instancia.nombre_instancia,
                        "ruta": ruta.path,
                        "error": res["error"]
                    })
                else:
                    summary["total_respaldos_registrados"] += res.get("registros_respaldo_creados", 0)
            except Exception as e:
                summary["errores"].append({
                    "servidor": servidor.nombre_servidor,
                    "instancia": instancia.nombre_instancia,
                    "ruta": ruta.path,
                    "error": str(e)
                })
                
    # Agregar un registro de auditoría global
    bitacora = Bitacora(
        entidad_afectada="Respaldo (Global Sync)",
        id_entidad=user_id,
        descripcion_evento=f"Sync global de respaldos finalizado. Rutas: {summary['total_rutas_procesadas']}, Respaldos creados: {summary['total_respaldos_registrados']}.",
        id_usuario=user_id,
        id_tipo_evento=6  # Descubrimiento / Tarea del sistema
    )
    db.add(bitacora)
    db.commit()
    
    return summary

def run_custom_server_integrated_file_discovery(db: Session, servidor_id: int, credencial_id: int, ruta_id: int, user_id: int, days: int = 0, deep: bool = True):
    """
    Descubrimiento PERSONALIZADO por servidor (Hot/Custom): Escanea backups de todas las instancias del servidor
    con parámetros opcionales de profundidad y antigüedad de días.
    """
    servidor = db.query(Servidor).filter(Servidor.id_servidor == servidor_id).first()
    ruta = db.query(RutaRespaldo).filter(RutaRespaldo.id_ruta == ruta_id).first()
    credencial = db.query(CredencialAcceso).filter(CredencialAcceso.id_credencial == credencial_id).first()
    
    if not servidor or not ruta or not credencial: 
        return {"error": "Servidor, Ruta o Credencial no encontrados"}
    
    # Validación de pertenencia de ruta
    if ruta.id_servidor != servidor.id_servidor:
        return {"error": f"La ruta {ruta.path} no pertenece al servidor {servidor.nombre_servidor}"}

    client = None
    try:
        client = get_ssh_connection(servidor, credencial, use_pool=True)
        
        maxdepth_clause = "" if deep else "-maxdepth 1"
        mtime_clause = f"-mtime -{days}" if days > 0 else ""
        
        found_files = []
        if not servidor.es_legacy:
            cmd = f"find {ruta.path} {maxdepth_clause} {mtime_clause} -type f -printf '%p|%s|%TY-%Tm-%Td %TH:%TM:%TS\\n' 2>/dev/null"
            output = discovery_provider.execute_command(client, cmd)
            if output:
                for line in output.split('\n'):
                    if '|' in line:
                        parts = line.split('|')
                        found_files.append({
                            "path": parts[0], 
                            "size": int(parts[1]),
                            "mtime": parts[2]
                        })
        else:
            cmd = f"find {ruta.path} {maxdepth_clause} {mtime_clause} -type f -exec ls -nl --time-style=long-iso {{}} \\; 2>/dev/null"
            output = discovery_provider.execute_command(client, cmd)
            if not output:
                cmd = f"find {ruta.path} {maxdepth_clause} {mtime_clause} -type f -exec ls -nl {{}} \\; 2>/dev/null"
                output = discovery_provider.execute_command(client, cmd)
            if output:
                for line in output.split('\n'):
                    parts = line.split()
                    if len(parts) >= 8:
                        try:
                            size = int(parts[4])
                            if "-" in parts[5]: # Long ISO
                                mtime = f"{parts[5]} {parts[6]}"
                                path_file = parts[7]
                            else: # Standard
                                mtime = f"{parts[5]} {parts[6]} {parts[7]}"
                                path_file = parts[8]
                            found_files.append({"path": path_file, "size": size, "mtime": mtime})
                        except: continue

        # Deduplicar
        seen_paths = set()
        dedup_files = []
        for f in found_files:
            if f["path"] not in seen_paths:
                seen_paths.add(f["path"])
                dedup_files.append(f)

        # Buscar todas las instancias de este servidor
        from app.models.infrastructure_models import InstanciaDBMS, BaseDeDatos
        instances = db.query(InstanciaDBMS).filter(InstanciaDBMS.id_servidor == servidor_id).all()
        instance_ids = [inst.id_instancia for inst in instances]
        databases = db.query(BaseDeDatos).filter(BaseDeDatos.id_instancia.in_(instance_ids)).all() if instance_ids else []

        results = []
        respaldos_creados = 0
        for bd in databases:
            # Buscar archivos de respaldo coincidentes
            matching_files = [f for f in dedup_files if bd.nombre_base.lower() in f["path"].lower()]
            
            # Obtener política
            asignacion = db.query(AsignacionPoliticaBD).filter(AsignacionPoliticaBD.id_base_datos == bd.id_base_datos).first()
            politica_nombre = "Sin política"
            id_politica = None
            if asignacion:
                politica = db.query(PoliticaRespaldo).filter(PoliticaRespaldo.id_politica == asignacion.id_politica).first()
                if politica:
                    politica_nombre = politica.nombre_politica
                    id_politica = politica.id_politica

            if matching_files:
                for f in matching_files:
                    file_path = f["path"]
                    size_mb = round(f["size"] / (1024 * 1024), 2)
                    file_name = file_path.split('/')[-1]
                    
                    if asignacion and id_politica:
                        # Evitar duplicados
                        existe = db.query(Respaldo).filter(
                            Respaldo.id_base_datos == bd.id_base_datos,
                            Respaldo.nombre_archivo == file_name,
                            Respaldo.path_fisico_actual == file_path
                        ).first()
                        if not existe:
                            nuevo_respaldo = Respaldo(
                                id_base_datos=bd.id_base_datos,
                                id_politica=id_politica,
                                id_credencial=credencial_id,
                                id_estado_ejecucion=4, # 4: Ejecutado/Exitoso
                                nombre_archivo=file_name,
                                tamano_mb=Decimal(str(size_mb)),
                                path_fisico_origen=file_path,
                                ubicacion_actual="Origen",
                                ip_almacenado_actual=servidor.direccion_ip,
                                path_fisico_actual=file_path,
                                fecha_fin=datetime.now()
                            )
                            db.add(nuevo_respaldo)
                            respaldos_creados += 1

                    results.append({
                        "base_datos_id": bd.id_base_datos,
                        "nombre_base": bd.nombre_base,
                        "politica_nombre": politica_nombre,
                        "ruta_path": file_path,
                        "archivo_encontrado": True,
                        "tamano_encontrado_mb": size_mb,
                        "timestamp_verificacion": datetime.now().isoformat(),
                        "detalle": "Respaldo verificado con éxito"
                    })
            else:
                results.append({
                    "base_datos_id": bd.id_base_datos,
                    "nombre_base": bd.nombre_base,
                    "politica_nombre": politica_nombre,
                    "ruta_path": None,
                    "archivo_encontrado": False,
                    "tamano_encontrado_mb": 0.0,
                    "timestamp_verificacion": datetime.now().isoformat(),
                    "detalle": "No se encontró archivo de respaldo reciente"
                })

        # Auditoría
        nueva_bitacora = Bitacora(
            entidad_afectada="Respaldo (Server Custom Check)", 
            id_entidad=servidor_id, 
            descripcion_evento=f"Escaneo personalizado SSH en {ruta.path} (days={days}, deep={deep}). Bases: {len(databases)}, Encontradas: {sum(1 for r in results if r['archivo_encontrado'])}", 
            id_usuario=user_id, 
            id_tipo_evento=6
        )
        db.add(nueva_bitacora)
        db.commit()

        return results
    finally:
        pass
