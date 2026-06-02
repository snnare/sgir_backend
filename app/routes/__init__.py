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
    Sincroniza en tiempo real las bases de datos de todos los servidores activos
    y genera un reporte CSV crudo con los datos descubiertos.
    No requiere autenticación y consulta los datos de forma global y automática.
    """
    import csv
    
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

__all__ = [
    "core_crud_router",
    "router"
]

