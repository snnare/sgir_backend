from apscheduler.schedulers.asyncio import AsyncIOScheduler
from concurrent.futures import ThreadPoolExecutor
from app.services.monitoring.scheduler_tasks import bulk_monitor_by_criticality, retention_policy_task
import logging

logger = logging.getLogger("scheduler_manager")

# Pool de hilos dedicado para tareas de I/O masivo (SSH/DB)
# Optimizado para 4-6 CPUs y gran volumen de conexiones paralelas
scheduler_executor = ThreadPoolExecutor(max_workers=80)

scheduler = AsyncIOScheduler()

def start_scheduler():
    """Configura e inicia las tareas programadas por criticidad (MODO TEST: SEGUNDOS)."""
    
    # 1. CRÍTICO: Cada 15 segundos
    scheduler.add_job(
        bulk_monitor_by_criticality, 
        'interval', 
        seconds=15, 
        args=[4], 
        id='monitor_critico',
        replace_existing=True
    )

    # 2. ALTO: Cada 20 segundos
    scheduler.add_job(
        bulk_monitor_by_criticality, 
        'interval', 
        seconds=20, 
        args=[3], 
        id='monitor_alto',
        replace_existing=True
    )

    # 3. MEDIO: Cada 25 segundos
    scheduler.add_job(
        bulk_monitor_by_criticality, 
        'interval', 
        seconds=25, 
        args=[2], 
        id='monitor_medio',
        replace_existing=True
    )

    # 4. BAJO: Cada 30 segundos
    scheduler.add_job(
        bulk_monitor_by_criticality, 
        'interval', 
        seconds=30, 
        args=[1], 
        id='monitor_bajo',
        replace_existing=True
    )

    # 5. RETENCIÓN: Limpieza de datos antiguos cada 24 horas (Ejemplo: 3 AM)
    scheduler.add_job(
        retention_policy_task,
        'cron',
        hour=3,
        minute=0,
        id='retention_policy',
        replace_existing=True
    )

    scheduler.start()
    logger.info("Scheduler de PRUEBA iniciado (Intervalos de 15-30 segundos).")

def stop_scheduler():
    """Detiene el scheduler y libera el pool de hilos."""
    scheduler.shutdown()
    scheduler_executor.shutdown(wait=True)
    logger.info("Scheduler y Pool de hilos detenidos.")
