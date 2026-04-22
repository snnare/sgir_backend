from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

# Conexión a Meta-DB (Postgres)
from app.db.postgres.postgres_connection import get_db as get_pg_db
# Modelos de Infraestructura
from app.models.infrastructure_models import InstanciaDBMS, Servidor, CredencialAcceso
# Core Dinámico y Seguridad
from app.core.dynamic_db_core import get_dynamic_session
from app.core.dependencies import get_current_user
# Servicios de Monitoreo y Schemas
from app.services.monitoring.mysql5.mysql5_service import get_mysql5_metrics
from app.schemas import (
    MySQL5Metrics as MySQL5FullMetrics
)

router = APIRouter(
    tags=["Monitoring - MySQL 5"],
    dependencies=[Depends(get_current_user)]
)

@router.get("/metrics/{id_instancia}", response_model=MySQL5FullMetrics)
def get_full_metrics(id_instancia: int, db: Session = Depends(get_pg_db)):
    """
    Obtiene métricas en tiempo real consultando la jerarquía:
    Instancia -> Servidor -> Credencial (Tipo DB Native)
    """
    
    # 1. Buscar la instancia y validar que sea MySQL 5 (id_dbms=2)
    instancia = db.query(InstanciaDBMS).filter(
        InstanciaDBMS.id_instancia == id_instancia,
        InstanciaDBMS.id_dbms == 2
    ).first()
    
    if not instancia:
        raise HTTPException(status_code=404, detail="Instancia MySQL 5 no encontrada o ID incorrecto")

    # 2. Obtener el servidor asociado
    servidor = instancia.servidor
    if not servidor:
        raise HTTPException(status_code=404, detail="Servidor no asociado a la instancia")

    # 3. Buscar una credencial activa de tipo "DB Native" (ID 2) para este servidor
    credencial = db.query(CredencialAcceso).filter(
        CredencialAcceso.id_servidor == servidor.id_servidor,
        CredencialAcceso.id_tipo_acceso == 2,      # 2: DB Native
        CredencialAcceso.id_estado_credencial == 1 # 1: Activo
    ).first()

    if not credencial:
        raise HTTPException(
            status_code=404, 
            detail=f"No hay credenciales de Base de Datos activas para el servidor {servidor.direccion_ip}"
        )

    # 4. Conexión Dinámica y Extracción de Métricas
    try:
        # Pasamos servidor, credencial e id_dbms (2) al core
        remote_session = get_dynamic_session(servidor, credencial, instancia.id_dbms)
        
        # Extraer métricas usando la sesión del servidor remoto
        metrics = get_mysql5_metrics(remote_session)
        return metrics
        
    except Exception as e:
        raise HTTPException(
            status_code=500, 
            detail=f"Error de monitoreo en {servidor.direccion_ip}:{instancia.puerto} -> {str(e)}"
        )
    finally:
        if 'remote_session' in locals():
            remote_session.close()
