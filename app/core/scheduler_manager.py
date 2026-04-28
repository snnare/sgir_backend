from apscheduler.schedulers.asyncio import AsyncIOScheduler
from concurrent.futures import ThreadPoolExecutor
from app.services.monitoring.scheduler_tasks import bulk_monitor_by_criticality
import logging

logger = logging.getLogger("scheduler_manager")

# Pool de hilos dedicado para tareas de I/O masivo (SSH/DB)
# Optimizado para 4-6 CPUs y gran volumen de conexiones paralelas
scheduler_executor = ThreadPoolExecutor(max_workers=80)

scheduler = AsyncIOScheduler()

def start_scheduler():
    """Configura e inicia las tareas programadas por criticidad."""
    
    # 1. CRÍTICO: Cada 1 minuto (ID 4 en seed)
    scheduler.add_job(
        bulk_monitor_by_criticality, 
        'interval', 
        minutes=1, 
        args=[4], 
        id='monitor_critico',
        replace_existing=True
    )

    # 2. ALTO: Cada 5 minutos (ID 3 en seed)
    scheduler.add_job(
        bulk_monitor_by_criticality, 
        'interval', 
        minutes=5, 
        args=[3], 
        id='monitor_alto',
        replace_existing=True
    )

    # 3. MEDIO: Cada 15 minutos (ID 2 en seed)
    scheduler.add_job(
        bulk_monitor_by_criticality, 
        'interval', 
        minutes=15, 
        args=[2], 
        id='monitor_medio',
        replace_existing=True
    )

    # 4. BAJO: Cada 60 minutos (ID 1 en seed)
    scheduler.add_job(
        bulk_monitor_by_criticality, 
        'interval', 
        minutes=60, 
        args=[1], 
        id='monitor_bajo',
        replace_existing=True
    )

    scheduler.start()
    logger.info("Scheduler iniciado correctamente con 80 workers disponibles.")

def stop_scheduler():
    """Detiene el scheduler y libera el pool de hilos."""
    scheduler.shutdown()
    scheduler_executor.shutdown(wait=True)
    logger.info("Scheduler y Pool de hilos detenidos.")
