from sqlalchemy.orm import Session
from app.models.monitoring_persistence_models import Monitoreo, Metrica, TipoMetrica
from app.models.infrastructure_models import Servidor, CredencialAcceso
from app.core.dynamic_ssh_core import get_ssh_client
from datetime import datetime
from decimal import Decimal

def execute_ssh_command(client, command: str) -> str:
    """
    EJECUTOR DE COMANDOS: Ejecuta el comando SSH y devuelve el stdout.
    """
    stdin, stdout, stderr = client.exec_command(command)
    return stdout.read().decode('utf-8').strip()

def extract_host_metrics(client, es_legacy: bool):
    """
    EXTRACTOR DE METRICAS: Selecciona los comandos adecuados según la versión del SO.
    Compatible con RHEL 4 en adelante.
    """
    metrics = {}
    
    # Comandos segun si es Legacy o Moderno
    if es_legacy:
        # En sistemas viejos (RHEL 4), /proc/stat es lo más directo
        cpu_cmd = "top -bn1 | grep 'Cpu(s)' | awk '{print $2}' | sed 's/%us,//'"
        ram_cmd = "free -m | grep Mem | awk '{print ($3/$2)*100.0}'"
        disk_cmd = "df -h / | tail -1 | awk '{print $5}' | sed 's/%//'"
    else:
        # Moderno (Fedora, RHEL 7+)
        cpu_cmd = "top -bn1 | grep 'Cpu(s)' | awk '{print $2 + $4}' | sed 's/,/./'"
        ram_cmd = "free | grep Mem | awk '{print $3/$2 * 100.0}' | sed 's/,/./'"
        disk_cmd = "df -h / | tail -1 | awk '{print $5}' | sed 's/%//' | sed 's/,/./'"

    # 1. CPU
    try:
        val = float(execute_ssh_command(client, cpu_cmd))
        metrics['CPU_Usage'] = Decimal(str(round(val, 2)))
    except:
        metrics['CPU_Usage'] = Decimal("0.0")

    # 2. RAM
    try:
        val = float(execute_ssh_command(client, ram_cmd))
        metrics['RAM_Usage'] = Decimal(str(round(val, 2)))
    except:
        metrics['RAM_Usage'] = Decimal("0.0")

    # 3. Disk
    try:
        val = float(execute_ssh_command(client, disk_cmd))
        metrics['Disk_Usage'] = Decimal(str(round(val, 2)))
    except:
        metrics['Disk_Usage'] = Decimal("0.0")

    # 4. Uptime (Universal)
    try:
        val = float(execute_ssh_command(client, "awk '{print $1/86400}' /proc/uptime").replace(',', '.'))
        metrics['Uptime'] = Decimal(str(round(val, 2)))
    except:
        metrics['Uptime'] = Decimal("0.0")

    return metrics

def run_ssh_monitoring(db_local: Session, servidor_id: int, credencial_id: int):
    """
    ORQUESTADOR: Valida, Conecta, Ejecuta y Persiste.
    """
    servidor = db_local.query(Servidor).filter(Servidor.id_servidor == servidor_id).first()
    credencial = db_local.query(CredencialAcceso).filter(CredencialAcceso.id_credencial == credencial_id).first()

    if not servidor or not credencial:
        return {"error": "Servidor o Credencial no encontrados"}

    # Iniciar registro en Monitoreo (id_estado_monitoreo=1: Activo)
    nuevo_monitoreo = Monitoreo(
        id_servidor=servidor_id,
        id_credencial=credencial_id,
        id_estado_monitoreo=1 
    )
    db_local.add(nuevo_monitoreo)
    db_local.commit()
    db_local.refresh(nuevo_monitoreo)

    client = None
    try:
        # 1. CONECTAR
        client = get_ssh_client(servidor, credencial)
        
        # 2. EJECUTAR (con logica de legacy)
        raw_metrics = extract_host_metrics(client, servidor.es_legacy)

        # 3. PERSISTIR (Modelo Fisico)
        for nombre, valor in raw_metrics.items():
            tipo = db_local.query(TipoMetrica).filter(TipoMetrica.nombre_tipo == nombre).first()
            if not tipo:
                tipo = TipoMetrica(nombre_tipo=nombre, unidad_medida="%" if "Usage" in nombre else "Días")
                db_local.add(tipo)
                db_local.commit()
                db_local.refresh(tipo)

            db_local.add(Metrica(
                valor=valor,
                id_monitoreo=nuevo_monitoreo.id_monitoreo,
                id_tipo_metrica=tipo.id_tipo_metrica
            ))

        # Finalizar
        nuevo_monitoreo.fecha_fin = datetime.now()
        nuevo_monitoreo.id_estado_monitoreo = 2 # Completado
        db_local.commit()

        return {
            "monitoreo_id": nuevo_monitoreo.id_monitoreo,
            "servidor": servidor.nombre_servidor,
            "legacy": servidor.es_legacy,
            "metrics": raw_metrics,
            "status": "success"
        }

    except Exception as e:
        nuevo_monitoreo.id_estado_monitoreo = 3 # Fallido
        db_local.commit()
        raise e
    finally:
        if client:
            client.close()
