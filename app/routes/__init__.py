from .core_crud import router as core_crud_router
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from app.db.postgres.postgres_connection import get_db as get_pg_db
from app.models.infrastructure_models import BaseDeDatos, InstanciaDBMS, DBMS, Servidor
import io

router = APIRouter(tags=["Reports"])

@router.get("/assets/pdf")
def get_assets_pdf(db: Session = Depends(get_pg_db)):
    """
    Sincroniza en tiempo real las bases de datos de todos los servidores activos
    y genera un reporte PDF profesional en formato A4 con los datos descubiertos.
    No requiere autenticación y consulta los datos de forma global y automática.
    """
    # 1. Ejecutar el auto-descubrimiento en tiempo real para asegurar datos frescos
    try:
        from app.services.infrastructure.inventory_sync_service import run_bulk_inventory_sync
        run_bulk_inventory_sync(db)
    except Exception:
        # En caso de fallo de conexión de red externa, procedemos con los datos cacheados
        pass
    
    # 2. Consultar las bases de datos activas en la CMDB local ordenadas por motor de BD
    query = db.query(
        Servidor.direccion_ip,
        DBMS.nombre_dbms,
        DBMS.version,
        BaseDeDatos.nombre_base,
        BaseDeDatos.tamano_mb
    ).select_from(BaseDeDatos)\
     .join(InstanciaDBMS, BaseDeDatos.id_instancia == InstanciaDBMS.id_instancia)\
     .join(Servidor, InstanciaDBMS.id_servidor == Servidor.id_servidor)\
     .join(DBMS, InstanciaDBMS.id_dbms == DBMS.id_dbms)\
     .filter(BaseDeDatos.id_estado_bd == 1)\
     .order_by(DBMS.nombre_dbms, Servidor.direccion_ip, BaseDeDatos.nombre_base)
     
    resultados = query.all()
    
    # 3. Formatear la lista de bases de datos para el PDF
    databases_data = []
    total_size = 0.0
    for r in resultados:
        tamano = float(r.tamano_mb or 0)
        
        # Normalizar el nombre del RDBMS
        motor_raw = r.nombre_dbms.lower()
        if "mysql" in motor_raw:
            rdbms_name = "MySQL"
        elif "mongo" in motor_raw:
            rdbms_name = "MongoDB"
        elif "oracle" in motor_raw:
            rdbms_name = "Oracle"
        else:
            rdbms_name = r.nombre_dbms.split()[0]

        # Extraer la versión principal (ej. "8.0.32" -> "8", "21c" -> "21c")
        version_parts = []
        for char in r.version:
            if char.isdigit():
                version_parts.append(char)
            elif char == '.' or not char.isalnum():
                break
            else:
                version_parts.append(char)
                break
        version_str = "".join(version_parts) if version_parts else r.version

        motor_display = f"{rdbms_name} {version_str}"
        
        databases_data.append({
            "ip": r.direccion_ip,
            "motor": motor_display,
            "nombre": r.nombre_base,
            "tamano_mb": tamano
        })
        total_size += tamano

    # 4. Generar el PDF
    try:
        from app.services.reports.pdf_service import generate_db_inventory_pdf
        pdf_bytes = generate_db_inventory_pdf(databases_data, total_size, "Administrador de Sistemas (DTIC)")
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error al generar el reporte PDF: {str(e)}"
        )
        
    # 5. Retornar el archivo PDF generado en caliente
    return StreamingResponse(
        io.BytesIO(pdf_bytes),
        media_type="application/pdf",
        headers={
            "Content-Disposition": "attachment; filename=reporte_inventario_dbs.pdf"
        }
    )

@router.get("/assets/pdf-offline")
def get_assets_pdf_offline(db: Session = Depends(get_pg_db)):
    """
    Genera un reporte PDF profesional en formato A4 consultando
    directamente los datos de la CMDB en la base de datos PostgreSQL local,
    sin conectarse en tiempo real a los servidores remotos (Offline).
    """
    # 1. Consultar las bases de datos activas en la CMDB local ordenadas por motor de BD
    query = db.query(
        Servidor.direccion_ip,
        DBMS.nombre_dbms,
        DBMS.version,
        BaseDeDatos.nombre_base,
        BaseDeDatos.tamano_mb
    ).select_from(BaseDeDatos)\
     .join(InstanciaDBMS, BaseDeDatos.id_instancia == InstanciaDBMS.id_instancia)\
     .join(Servidor, InstanciaDBMS.id_servidor == Servidor.id_servidor)\
     .join(DBMS, InstanciaDBMS.id_dbms == DBMS.id_dbms)\
     .filter(BaseDeDatos.id_estado_bd == 1)\
     .order_by(DBMS.nombre_dbms, Servidor.direccion_ip, BaseDeDatos.nombre_base)
     
    resultados = query.all()
    
    # 2. Formatear la lista de bases de datos para el PDF
    databases_data = []
    total_size = 0.0
    for r in resultados:
        tamano = float(r.tamano_mb or 0)
        
        # Normalizar el nombre del RDBMS
        motor_raw = r.nombre_dbms.lower()
        if "mysql" in motor_raw:
            rdbms_name = "MySQL"
        elif "mongo" in motor_raw:
            rdbms_name = "MongoDB"
        elif "oracle" in motor_raw:
            rdbms_name = "Oracle"
        else:
            rdbms_name = r.nombre_dbms.split()[0]

        # Extraer la versión principal (ej. "8.0.32" -> "8", "21c" -> "21c")
        version_parts = []
        for char in r.version:
            if char.isdigit():
                version_parts.append(char)
            elif char == '.' or not char.isalnum():
                break
            else:
                version_parts.append(char)
                break
        version_str = "".join(version_parts) if version_parts else r.version

        motor_display = f"{rdbms_name} {version_str}"
        
        databases_data.append({
            "ip": r.direccion_ip,
            "motor": motor_display,
            "nombre": r.nombre_base,
            "tamano_mb": tamano
        })
        total_size += tamano

    # 3. Generar el PDF
    try:
        from app.services.reports.pdf_service import generate_db_inventory_pdf
        pdf_bytes = generate_db_inventory_pdf(databases_data, total_size, "Administrador de Sistemas (DTIC) - Reporte Offline")
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error al generar el reporte PDF offline: {str(e)}"
        )
        
    # 4. Retornar el archivo PDF generado
    return StreamingResponse(
        io.BytesIO(pdf_bytes),
        media_type="application/pdf",
        headers={
            "Content-Disposition": "attachment; filename=reporte_inventario_dbs_offline.pdf"
        }
    )

@router.get("/assets/csv")
def get_assets_csv(db: Session = Depends(get_pg_db)):
    """
    Genera un reporte CSV crudo con los datos descubiertos consultando
    directamente la CMDB en la base de datos PostgreSQL local,
    sin conectarse en tiempo real a los servidores remotos (Offline).
    No requiere autenticación.
    """
    import csv
    
    # 1. Consultar las bases de datos activas en la CMDB local ordenadas por motor de BD
    query = db.query(
        Servidor.direccion_ip,
        DBMS.nombre_dbms,
        DBMS.version,
        BaseDeDatos.nombre_base,
        BaseDeDatos.tamano_mb
    ).select_from(BaseDeDatos)\
     .join(InstanciaDBMS, BaseDeDatos.id_instancia == InstanciaDBMS.id_instancia)\
     .join(Servidor, InstanciaDBMS.id_servidor == Servidor.id_servidor)\
     .join(DBMS, InstanciaDBMS.id_dbms == DBMS.id_dbms)\
     .filter(BaseDeDatos.id_estado_bd == 1)\
     .order_by(DBMS.nombre_dbms, Servidor.direccion_ip, BaseDeDatos.nombre_base)
     
    resultados = query.all()
    
    # 3. Generar el archivo CSV en memoria
    output = io.StringIO()
    writer = csv.writer(output, delimiter=',', quoting=csv.QUOTE_MINIMAL)
    
    # Escribir encabezados
    writer.writerow(["Direccion IP", "Motor DBMS", "Base de Datos", "Tamano (MB)"])
    
    # Escribir registros
    for r in resultados:
        tamano = float(r.tamano_mb or 0)
        
        # Normalizar el nombre del RDBMS
        motor_raw = r.nombre_dbms.lower()
        if "mysql" in motor_raw:
            rdbms_name = "MySQL"
        elif "mongo" in motor_raw:
            rdbms_name = "MongoDB"
        elif "oracle" in motor_raw:
            rdbms_name = "Oracle"
        else:
            rdbms_name = r.nombre_dbms.split()[0]

        # Extraer la versión principal
        version_parts = []
        for char in r.version:
            if char.isdigit():
                version_parts.append(char)
            elif char == '.' or not char.isalnum():
                break
            else:
                version_parts.append(char)
                break
        version_str = "".join(version_parts) if version_parts else r.version

        motor_display = f"{rdbms_name} {version_str}"
        
        writer.writerow([r.direccion_ip, motor_display, r.nombre_base, f"{tamano:.2f}"])
        
    # Colocar el cursor al inicio del buffer
    output.seek(0)
    
    # 4. Retornar el archivo CSV (codificado en utf-8-sig para compatibilidad con Excel)
    return StreamingResponse(
        io.BytesIO(output.getvalue().encode('utf-8-sig')),
        media_type="text/csv",
        headers={
            "Content-Disposition": "attachment; filename=reporte_inventario_dbs.csv"
        }
    )

@router.get("/assets/sre-pdf-offline")
def get_assets_sre_pdf_offline(db: Session = Depends(get_pg_db)):
    """
    Genera un reporte PDF consolidado general de SRE de forma offline,
    obteniendo el estado de salud, alertas y el inventario de bases de datos de la CMDB local.
    """
    from app.models.infrastructure_models import Servidor, BaseDeDatos, InstanciaDBMS, DBMS, NivelCriticidad
    from app.models.monitoring_persistence_models import Monitoreo, Metrica, Alerta
    from app.services.monitoring.ssh_service import LIVE_METRICS_CACHE
    from datetime import datetime, timezone, timedelta
    
    # 1. Obtener todos los servidores activos con su nivel de criticidad
    servidores_db = db.query(Servidor, NivelCriticidad).join(
        NivelCriticidad, Servidor.id_nivel_criticidad == NivelCriticidad.id_nivel_criticidad
    ).filter(Servidor.id_estado_servidor == 1).all()
    
    servidores_data = []
    for srv, crit in servidores_db:
        # Recuperar última sesión de monitoreo de host
        last_session = db.query(Monitoreo).filter(
            Monitoreo.id_servidor == srv.id_servidor,
            Monitoreo.id_estado_monitoreo == 4
        ).order_by(Monitoreo.id_monitoreo.desc()).first()
        
        # Calcular estado SRE y frescura
        is_stale = True
        status_sre = "stale"
        if last_session:
            ahora = datetime.now(timezone.utc)
            fecha_inicio = last_session.fecha_inicio
            if fecha_inicio.tzinfo is None:
                fecha_inicio = fecha_inicio.replace(tzinfo=timezone.utc)
            diferencia = ahora - fecha_inicio
            is_stale = diferencia > timedelta(minutes=5)
            
            if not is_stale:
                # Si no es stale, checar incidentes (>90% de uso)
                has_incident = db.query(Metrica).filter(Metrica.id_monitoreo == last_session.id_monitoreo).first()
                status_sre = "critical" if has_incident else "healthy"
            else:
                status_sre = "stale"
        else:
            status_sre = "stale" # Fallback si nunca ha sido monitoreado
            
        # Decodificar métricas en vivo (Live Cache RAM)
        live_data = LIVE_METRICS_CACHE.get(srv.id_servidor)
        cpu_val = 0.0
        ram_val = 0.0
        if live_data and isinstance(live_data, str):
            try:
                parts = live_data.split("|")
                cpu_val = float(parts[0])
                ram_val = float(parts[1])
            except Exception:
                pass
                
        servidores_data.append({
            "nombre": srv.nombre_servidor,
            "ip": srv.direccion_ip,
            "cpu": cpu_val,
            "ram": ram_val,
            "criticidad": crit.nombre_nivel,
            "status_sre": status_sre
        })
        
    # 2. Consultar alertas activas en la BD (estado = 1)
    total_alerts = db.query(Alerta).filter(Alerta.id_estado_alerta == 1).count()
    
    # 3. Consultar bases de datos activas
    bd_resultados = db.query(
        Servidor.direccion_ip,
        DBMS.nombre_dbms,
        DBMS.version,
        BaseDeDatos.nombre_base,
        BaseDeDatos.tamano_mb
    ).select_from(BaseDeDatos)\
     .join(InstanciaDBMS, BaseDeDatos.id_instancia == InstanciaDBMS.id_instancia)\
     .join(Servidor, InstanciaDBMS.id_servidor == Servidor.id_servidor)\
     .join(DBMS, InstanciaDBMS.id_dbms == DBMS.id_dbms)\
     .filter(BaseDeDatos.id_estado_bd == 1)\
     .order_by(DBMS.nombre_dbms, Servidor.direccion_ip, BaseDeDatos.nombre_base).all()
     
    databases_data = []
    for r in bd_resultados:
        tamano = float(r.tamano_mb or 0)
        
        # Normalizar el nombre del RDBMS
        motor_raw = r.nombre_dbms.lower()
        if "mysql" in motor_raw:
            rdbms_name = "MySQL"
        elif "mongo" in motor_raw:
            rdbms_name = "MongoDB"
        elif "oracle" in motor_raw:
            rdbms_name = "Oracle"
        else:
            rdbms_name = r.nombre_dbms.split()[0]

        # Extraer la versión principal
        version_parts = []
        for char in r.version:
            if char.isdigit():
                version_parts.append(char)
            elif char == '.' or not char.isalnum():
                break
            else:
                version_parts.append(char)
                break
        version_str = "".join(version_parts) if version_parts else r.version
        motor_display = f"{rdbms_name} {version_str}"
        
        databases_data.append({
            "ip": r.direccion_ip,
            "motor": motor_display,
            "nombre": r.nombre_base,
            "tamano_mb": f"{tamano:,.2f}"
        })
        
    # 4. Generar el PDF
    try:
        from app.services.reports.pdf_service import generate_general_sre_pdf
        pdf_bytes = generate_general_sre_pdf(
            servidores=servidores_data,
            databases=databases_data,
            total_alerts=total_alerts,
            usuario_nombre="Administrador de Sistemas (SRE)"
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error al generar el reporte general SRE PDF: {str(e)}"
        )
        
    return StreamingResponse(
        io.BytesIO(pdf_bytes),
        media_type="application/pdf",
        headers={
            "Content-Disposition": "attachment; filename=reporte_general_sre.pdf"
        }
    )

@router.get("/assets/sre-sla-pdf")
def get_assets_sre_sla_pdf(db: Session = Depends(get_pg_db)):
    """
    Genera un reporte PDF consolidado mensual de SLA, incidentes y disponibilidad (Offline).
    """
    from app.models.infrastructure_models import Servidor
    from app.models.monitoring_persistence_models import Monitoreo, Metrica, Alerta, NivelAlerta
    from app.models.user_models import UserStatus
    from datetime import datetime, timezone, timedelta
    
    # 1. Obtener todos los servidores activos
    servidores_db = db.query(Servidor).filter(Servidor.id_estado_servidor == 1).all()
    
    servidores_sla = []
    lowest_sla = 100.0
    lowest_sla_name = "N/D"
    
    for srv in servidores_db:
        # Contar chequeos exitosos y fallidos
        total_checks = db.query(Monitoreo).filter(Monitoreo.id_servidor == srv.id_servidor).count()
        success_checks = db.query(Monitoreo).filter(
            Monitoreo.id_servidor == srv.id_servidor,
            Monitoreo.id_estado_monitoreo == 4
        ).count()
        
        failed_checks = total_checks - success_checks
        
        if total_checks > 0:
            sla_percent = round((success_checks / total_checks) * 100, 2)
        else:
            sla_percent = 100.0
            
        servidores_sla.append({
            "nombre": srv.nombre_servidor,
            "ip": srv.direccion_ip,
            "total_checks": total_checks,
            "success_checks": success_checks,
            "failed_checks": failed_checks,
            "sla_percent": sla_percent
        })
        
        if sla_percent < lowest_sla:
            lowest_sla = sla_percent
            lowest_sla_name = f"{srv.nombre_servidor} ({sla_percent}%)"
            
    # Calcular SLA promedio
    average_sla = round(sum(s["sla_percent"] for s in servidores_sla) / len(servidores_sla), 2) if servidores_sla else 100.0
    
    # 2. Obtener historial de alertas e incidentes (últimas 30 alertas)
    alertas_db = db.query(Alerta, Servidor, NivelAlerta, UserStatus).join(
        Servidor, Alerta.id_servidor == Servidor.id_servidor
    ).join(
        NivelAlerta, Alerta.id_nivel_alerta == NivelAlerta.id_nivel_alerta
    ).join(
        UserStatus, Alerta.id_estado_alerta == UserStatus.id_estado
    ).order_by(Alerta.fecha_alerta.desc()).limit(30).all()
    
    incidentes = []
    total_incidents = len(alertas_db)
    
    for alerta, srv, nivel, estado in alertas_db:
        fecha_alerta = alerta.fecha_alerta
        fecha_str = fecha_alerta.strftime("%Y-%m-%d %H:%M:%S") if fecha_alerta else "N/D"
        
        incidentes.append({
            "fecha": fecha_str,
            "servidor": srv.nombre_servidor,
            "ip": srv.direccion_ip,
            "descripcion": alerta.descripcion,
            "nivel_alerta": nivel.nombre_nivel,
            "estado": estado.nombre_estado
        })
        
    # Calcular días en historial
    first_mon = db.query(Monitoreo).order_by(Monitoreo.fecha_inicio.asc()).first()
    last_mon = db.query(Monitoreo).order_by(Monitoreo.fecha_inicio.desc()).first()
    total_days = 30
    if first_mon and last_mon:
        diff = last_mon.fecha_inicio - first_mon.fecha_inicio
        total_days = max(1, diff.days)
        
    # 3. Generar el PDF
    try:
        from app.services.reports.pdf_service import generate_sre_sla_pdf
        pdf_bytes = generate_sre_sla_pdf(
            servidores_sla=servidores_sla,
            incidentes=incidentes,
            average_sla=average_sla,
            total_incidents=total_incidents,
            total_days=total_days,
            lowest_sla_srv=lowest_sla_name if lowest_sla_name != "N/D" else "Ninguno",
            usuario_nombre="Administrador SRE (DTIC UAEMex)"
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error al generar el reporte SRE SLA PDF: {str(e)}"
        )
        
    return StreamingResponse(
        io.BytesIO(pdf_bytes),
        media_type="application/pdf",
        headers={
            "Content-Disposition": "attachment; filename=reporte_sre_sla.pdf"
        }
    )

@router.get("/backups/pdf")
def get_backups_pdf(db: Session = Depends(get_pg_db)):
    """
    Sincroniza en tiempo real las bases de datos de todos los servidores activos,
    descubre/verifica respaldos y genera un reporte PDF profesional en formato A4 landscape.
    """
    try:
        from app.services.infrastructure.inventory_sync_service import run_bulk_inventory_sync
        run_bulk_inventory_sync(db)
    except Exception:
        pass

    from app.services.backups.backup_crud import get_historial_respaldos_enriquecido
    backups_data = get_historial_respaldos_enriquecido(db)
    
    total_size = sum(float(b.get("tamano_mb") or 0.0) for b in backups_data)

    try:
        from app.services.reports.pdf_service import generate_backup_report_pdf
        pdf_bytes = generate_backup_report_pdf(backups_data, total_size, "Administrador de Sistemas (DTIC)")
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error al generar el reporte PDF de respaldos: {str(e)}"
        )
        
    return StreamingResponse(
        io.BytesIO(pdf_bytes),
        media_type="application/pdf",
        headers={
            "Content-Disposition": "attachment; filename=reporte_respaldos_dbs.pdf"
        }
    )

@router.get("/backups/pdf-offline")
def get_backups_pdf_offline(db: Session = Depends(get_pg_db)):
    """
    Genera un reporte PDF profesional de respaldos en formato A4 landscape,
    consultando directamente los datos persistidos en PostgreSQL local (Offline).
    """
    from app.services.backups.backup_crud import get_historial_respaldos_enriquecido
    backups_data = get_historial_respaldos_enriquecido(db)
    
    total_size = sum(float(b.get("tamano_mb") or 0.0) for b in backups_data)

    try:
        from app.services.reports.pdf_service import generate_backup_report_pdf
        pdf_bytes = generate_backup_report_pdf(backups_data, total_size, "Administrador de Sistemas (DTIC) - Reporte Offline")
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error al generar el reporte PDF offline de respaldos: {str(e)}"
        )
        
    return StreamingResponse(
        io.BytesIO(pdf_bytes),
        media_type="application/pdf",
        headers={
            "Content-Disposition": "attachment; filename=reporte_respaldos_dbs_offline.pdf"
        }
    )

@router.get("/backups/csv")
def get_backups_csv(db: Session = Depends(get_pg_db)):
    """
    Genera un reporte CSV con el historial enriquecido de respaldos físicos.
    """
    import csv
    from app.services.backups.backup_crud import get_historial_respaldos_enriquecido
    backups_data = get_historial_respaldos_enriquecido(db)
    
    output = io.StringIO()
    writer = csv.writer(output, delimiter=',', quoting=csv.QUOTE_MINIMAL)
    
    # Escribir encabezados
    writer.writerow(["Servidor", "Direccion IP", "Motor DBMS", "Archivo de Respaldo", "Tamano (MB)", "Estado Ejecucion", "Fecha Descubrimiento"])
    
    # Escribir registros
    for b in backups_data:
        writer.writerow([
            b.get("servidor"),
            b.get("ip"),
            b.get("motor"),
            b.get("nombre_archivo"),
            f"{float(b.get('tamano_mb') or 0.0):.2f}",
            b.get("estado_ejecucion"),
            b.get("fecha_descubrimiento")
        ])
        
    output.seek(0)
    
    return StreamingResponse(
        io.BytesIO(output.getvalue().encode('utf-8-sig')),
        media_type="text/csv",
        headers={
            "Content-Disposition": "attachment; filename=reporte_respaldos_dbs.csv"
        }
    )

__all__ = [
    "core_crud_router",
    "router"
]


