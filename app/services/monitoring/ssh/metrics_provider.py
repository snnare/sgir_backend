from decimal import Decimal

def execute_command(client, command: str) -> str:
    stdin, stdout, stderr = client.exec_command(command)
    return stdout.read().decode('utf-8').strip()

def get_metrics_modern(client, partition_paths: list[str] = None) -> dict:
    """
    Extracción de métricas para sistemas modernos (RHEL 7+, Debian, etc.)
    """
    if not partition_paths:
        partition_paths = ["/"]

    metrics = {}
    
    # CPU: % uso sumando user y system
    cpu_cmd = "top -bn1 | grep 'Cpu(s)' | awk '{print $2 + $4}' | sed 's/,/./'"
    # RAM: % uso
    ram_cmd = "free | grep Mem | awk '{print $3/$2 * 100.0}' | sed 's/,/./'"

    try:
        val = float(execute_command(client, cpu_cmd))
        metrics['CPU_Usage'] = Decimal(str(round(val, 2)))
    except:
        metrics['CPU_Usage'] = Decimal("0.0")

    try:
        val = float(execute_command(client, ram_cmd))
        metrics['RAM_Usage'] = Decimal(str(round(val, 2)))
    except:
        metrics['RAM_Usage'] = Decimal("0.0")

    # Disco: Procesar cada partición
    for path in partition_paths:
        disk_cmd = f"df -h {path} | tail -1 | awk '{{print $5}}' | sed 's/%//' | sed 's/,/./'"
        try:
            val = float(execute_command(client, disk_cmd))
            metrics[f'Disk_Usage({path})'] = Decimal(str(round(val, 2)))
        except:
            metrics[f'Disk_Usage({path})'] = Decimal("0.0")

    # Uptime universal
    try:
        val = float(execute_command(client, "awk '{print $1/86400}' /proc/uptime").replace(',', '.'))
        metrics['Uptime'] = Decimal(str(round(val, 2)))
    except:
        metrics['Uptime'] = Decimal("0.0")

    return metrics

def get_metrics_legacy(client, partition_paths: list[str] = None) -> dict:
    """
    Extracción de métricas para sistemas antiguos (RHEL 4/5)
    """
    if not partition_paths:
        partition_paths = ["/"]

    metrics = {}
    
    # CPU: En legacy top -bn1 suele tener el formato diferente
    cpu_cmd = "top -bn1 | grep 'Cpu(s)' | awk '{print $2}' | sed 's/%us,//' | sed 's/,/./'"
    # RAM: free -m es más seguro en legacy
    ram_cmd = "free -m | grep Mem | awk '{print ($3/$2)*100.0}' | sed 's/,/./'"

    try:
        val = float(execute_command(client, cpu_cmd))
        metrics['CPU_Usage'] = Decimal(str(round(val, 2)))
    except:
        metrics['CPU_Usage'] = Decimal("0.0")

    try:
        val = float(execute_command(client, ram_cmd))
        metrics['RAM_Usage'] = Decimal(str(round(val, 2)))
    except:
        metrics['RAM_Usage'] = Decimal("0.0")

    # Disco: Procesar cada partición
    for path in partition_paths:
        disk_cmd = f"df -h {path} | tail -1 | awk '{{print $5}}' | sed 's/%//' | sed 's/,/./'"
        try:
            val = float(execute_command(client, disk_cmd))
            metrics[f'Disk_Usage({path})'] = Decimal(str(round(val, 2)))
        except:
            metrics[f'Disk_Usage({path})'] = Decimal("0.0")

    try:
        val = float(execute_command(client, "awk '{print $1/86400}' /proc/uptime").replace(',', '.'))
        metrics['Uptime'] = Decimal(str(round(val, 2)))
    except:
        metrics['Uptime'] = Decimal("0.0")

    return metrics
