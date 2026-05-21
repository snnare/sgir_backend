from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.db.postgres.postgres_connection import get_db as get_pg_db
from app.services.monitoring.mysql5.mysql5_service import get_mysql5_metrics, run_mysql5_modular_monitoring
from app.core.dynamic_db_core import get_dynamic_session
from app.services import get_servidor, get_credencial
from app.schemas import MySQL5Metrics, MySQLModularMonitoringResponse
from app.core.dependencies import get_current_user
from app.models.infrastructure_models import InstanciaDBMS, CredencialAcceso

router = APIRouter(dependencies=[Depends(get_current_user)])

@router.get("/metrics/{id_instancia}", response_model=MySQL5Metrics)
def get_full_metrics(id_instancia: int, db: Session = Depends(get_pg_db)):
    """
    Obtiene métricas en tiempo real consultando la jerarquía:
    Instancia -> Servidor -> Credencial (Tipo DB Native)
    """
    instancia = db.query(InstanciaDBMS).filter(
        InstanciaDBMS.id_instancia == id_instancia,
        InstanciaDBMS.id_dbms == 2
    ).first()
    
    if not instancia:
        raise HTTPException(status_code=404, detail="Instancia MySQL 5 no encontrada o ID incorrecto")

    servidor = instancia.servidor
    if not servidor:
        raise HTTPException(status_code=404, detail="Servidor no asociado a la instancia")

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

    try:
        remote_session = get_dynamic_session(servidor, credencial, instancia.id_dbms)
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


@router.get("/{servidor_id}/{credencial_id}", response_model=MySQL5Metrics)
def monitor_mysql5(servidor_id: int, credencial_id: int, db: Session = Depends(get_pg_db)):
    """
    Realiza un monitoreo en tiempo real de una instancia MySQL 5 remota.
    """
    servidor = get_servidor(db, servidor_id)
    credencial = get_credencial(db, credencial_id)
    
    if not servidor or not credencial:
        raise HTTPException(status_code=404, detail="Servidor o credencial no encontrados")
    
    # 1. Crear sesión dinámica
    try:
        remote_db = get_dynamic_session(servidor, credencial)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al conectar al servidor remoto: {str(e)}")
    
    # 2. Extraer métricas
    try:
        metrics = get_mysql5_metrics(remote_db)
        return metrics
    finally:
        remote_db.close()

@router.get("/modular/{id_instancia}/{id_credencial}", response_model=MySQLModularMonitoringResponse)
def get_mysql5_modular_metrics(id_instancia: int, id_credencial: int, db: Session = Depends(get_pg_db)):
    """
    Obtiene métricas de MySQL 5 segmentadas por módulos (A, B, C) 
    según el nivel de criticidad del servidor registrado.
    """
    result = run_mysql5_modular_monitoring(db, id_instancia, id_credencial)
    
    if "error" in result:
        raise HTTPException(status_code=500, detail=result["error"])
        
    return result

