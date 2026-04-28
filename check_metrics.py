from app.db.postgres.postgres_connection import SessionLocal
from app.models.monitoring_persistence_models import Monitoreo, Metrica, TipoMetrica
from sqlalchemy import func

db = SessionLocal()
try:
    # 1. Buscar la última sesión de monitoreo del servidor 10
    last_session = db.query(Monitoreo).filter(Monitoreo.id_servidor == 10).order_by(Monitoreo.id_monitoreo.desc()).first()
    
    if last_session:
        print(f"Monitoreo ID: {last_session.id_monitoreo} | Fecha: {last_session.fecha_inicio}")
        print(f"Estado: {last_session.id_estado_monitoreo}")
        
        # 2. Consultar métricas asociadas
        metrics = db.query(Metrica, TipoMetrica).join(TipoMetrica).filter(Metrica.id_monitoreo == last_session.id_monitoreo).all()
        for m, t in metrics:
            print(f" - {t.nombre_tipo}: {m.valor} {t.unidad_medida}")
    else:
        print("No se encontraron sesiones de monitoreo para el Servidor 10.")
finally:
    db.close()
