from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.db.postgres.postgres_connection import get_db
from app.core.dependencies import get_current_user
from app.services.monitoring.ssh_service import (
    run_ssh_monitoring, 
    get_server_health_status, 
    get_global_health_summary,
    run_cron_discovery,
    run_filesystem_discovery,
    LIVE_METRICS_CACHE
)
from app.services import log_event
from app.models.user_models import User
from app.core.scheduler_manager import pause_scheduler, resume_scheduler, get_scheduler_status

m1_router = APIRouter()
m2_router = APIRouter()
m3_router = APIRouter()

@m2_router.get("/discover-cron/{servidor_id}/{credencial_id}")
def discover_cron(servidor_id: int, credencial_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """
    Escanea el crontab del servidor para sugerir políticas de respaldo.
    """
    result = run_cron_discovery(db, servidor_id, credencial_id)
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    return result

@m1_router.post("/discover-filesystems/{servidor_id}")
def discover_filesystems_endpoint(servidor_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """
    Lista los sistemas de archivos (puntos de montaje) reales del servidor.
    """
    result = run_filesystem_discovery(db, servidor_id)
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    return result

@m1_router.get("/scheduler/status")
def check_scheduler_status(current_user: User = Depends(get_current_user)):
    """Consulta si el scheduler está corriendo o pausado."""
    return {"status": get_scheduler_status()}

@m1_router.post("/scheduler/pause")
def pause_monitoring(current_user: User = Depends(get_current_user)):
    """Pausa el monitoreo automático. Solo Admin."""
    if current_user.id_rol != 1: # Asumiendo 1 es Admin
        raise HTTPException(status_code=403, detail="Privilegios insuficientes")
    success = pause_scheduler()
    if not success:
        return {"message": "El scheduler no estaba corriendo"}
    return {"message": "Monitoreo pausado exitosamente", "status": "paused"}

@m1_router.post("/scheduler/resume")
def resume_monitoring(current_user: User = Depends(get_current_user)):
    """Reanuda el monitoreo automático. Solo Admin."""
    if current_user.id_rol != 1:
        raise HTTPException(status_code=403, detail="Privilegios insuficientes")
    success = resume_scheduler()
    if not success:
        return {"message": "El scheduler ya estaba corriendo o falló la reanudación"}
    return {"message": "Monitoreo reanudado exitosamente", "status": "running"}

@m3_router.post("/scheduler/trigger-backup-retention")
def trigger_backup_retention(current_user: User = Depends(get_current_user)):
    """Ejecuta manualmente la política de retención de respaldos. Solo Admin."""
    if current_user.id_rol != 1:
        raise HTTPException(status_code=403, detail="Privilegios insuficientes")
    
    from app.services.monitoring.scheduler_tasks import backup_retention_task
    # Ejecutamos de forma síncrona para que el usuario reciba el resultado
    # Opcionalmente se podría enviar al executor si fuera muy pesada
    backup_retention_task()
    return {"message": "Política de retención de respaldos ejecutada exitosamente"}

@m1_router.get("/global-summary")

def get_global_summary(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Resumen consolidado de toda la infraestructura para el Dashboard.
    Retorna conteo de servidores sanos, críticos y desactualizados.
    """
    return get_global_health_summary(db)

@m1_router.get("/live-cache")
def get_live_metrics(current_user: User = Depends(get_current_user)):
    """
    Devuelve las métricas en tiempo real (CPU, RAM, Disco) de todos los servidores
    almacenadas en la caché global de memoria.
    """
    return LIVE_METRICS_CACHE

@m1_router.get("/health-status/{server_id}")
def check_health(
    server_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Consulta el estado de salud actual de un servidor basándose en la última
    sesión del scheduler y los umbrales de métricas (90%).
    """
    return get_server_health_status(db, server_id)

@m1_router.get("/{server_id}/{cred_id}")

def monitor_host_ssh(
    server_id: int,
    cred_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Ejecuta un monitoreo ad-hoc vía SSH en el servidor especificado.
    Extrae CPU, RAM, Disco y Uptime, persistiendo los datos en el modelo físico.
    """
    try:
        result = run_ssh_monitoring(db, server_id, cred_id)
        
        if "error" in result:
            raise HTTPException(status_code=404, detail=result["error"])
        
        # Auditoría del evento
        log_event(
            db, 
            user_id=current_user.id_usuario,
            entidad="Servidor", 
            entidad_id=server_id, 
            descripcion=f"Monitoreo SSH ejecutado exitosamente. ID Monitoreo: {result['monitoreo_id']}",
            tipo_evento_id=4 # 4: Ejecución según convención de auditoría
        )
        
        return result
        
    except Exception as e:
        # Auditoría del fallo
        log_event(
            db, 
            user_id=current_user.id_usuario,
            entidad="Servidor", 
            entidad_id=server_id, 
            descripcion=f"Fallo en monitoreo SSH: {str(e)}",
            tipo_evento_id=4
        )
        raise HTTPException(status_code=500, detail=str(e))
