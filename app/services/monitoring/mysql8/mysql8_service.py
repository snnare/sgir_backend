from sqlalchemy.orm import Session
from app.services.monitoring.mysql5.mysql5_service import get_mysql5_metrics
from app.schemas.monitoring_persistence_schemas import MySQL8Metrics

def get_mysql8_metrics(db: Session) -> MySQL8Metrics:
    """
    Extrae métricas de rendimiento de un servidor MySQL 8.
    Reutiliza la lógica base de MySQL 5 ya que los comandos SHOW GLOBAL STATUS son compatibles.
    """
    m5_data = get_mysql5_metrics(db)
    return MySQL8Metrics(**m5_data.model_dump())
