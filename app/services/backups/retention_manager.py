from sqlalchemy.orm import Session
from app.models.backup_models import Respaldo, PoliticaRespaldo
from app.models.user_models import UserStatus
from datetime import datetime, timedelta, timezone
import logging

logger = logging.getLogger("retention_manager")

def run_backup_retention_policy(db: Session):
    """
    Identifica y marca como 'Expirados' los registros de respaldo 
    que superen los días de retención definidos en su política.
    """
    try:
        # 1. Asegurar que existe el estado 'Expirado'
        status_expirado = db.query(UserStatus).filter(UserStatus.nombre_estado == "Expirado").first()
        
        if not status_expirado:
            status_expirado = UserStatus(nombre_estado="Expirado")
            db.add(status_expirado)
            db.commit()
            db.refresh(status_expirado)
            logger.info(f"Estado 'Expirado' creado con ID: {status_expirado.id_estado}")

        expirado_id = status_expirado.id_estado
        ahora = datetime.now(timezone.utc)

        # 2. Buscar respaldos que deben expirar
        # Unimos con la política para obtener los días de retención
        # Nota: id_estado_ejecucion se refiere a la tabla estado_general
        respaldos = db.query(Respaldo).join(PoliticaRespaldo).filter(
            Respaldo.id_estado_ejecucion != expirado_id
        ).all()

        count = 0
        for res in respaldos:
            # Calculamos la fecha límite: fecha_inicio + retencion_dias
            if not res.fecha_inicio:
                continue
                
            # Asumiendo que res.politica está disponible vía relationship o consultamos manualmente
            # En backup_models.py, Respaldo tiene id_politica pero no relationship explícita 'politica'
            # Vamos a consultarla si no está
            politica = db.query(PoliticaRespaldo).filter(PoliticaRespaldo.id_politica == res.id_politica).first()
            if not politica:
                continue

            fecha_limite = res.fecha_inicio + timedelta(days=politica.retencion_dias)
            
            if ahora > fecha_limite:
                res.id_estado_ejecucion = expirado_id
                count += 1

        if count > 0:
            db.commit()
            logger.info(f"Se marcaron {count} respaldos como 'Expirados'.")
        
        return count

    except Exception as e:
        db.rollback()
        logger.error(f"Error en run_backup_retention_policy: {str(e)}")
        raise e
