from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.db.postgres.postgres_connection import get_db
from app.core.dependencies import get_current_user
from app.services.monitoring.ssh_service import run_ssh_monitoring
from app.services import log_event
from app.models.user_models import User

router = APIRouter()

@router.get("/{server_id}/{cred_id}")
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
