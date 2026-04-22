from decimal import Decimal

def execute_command(client, command: str) -> str:
    stdin, stdout, stderr = client.exec_command(command)
    return stdout.read().decode('utf-8').strip()

def get_metrics_modern(client) -> dict:
    """
    Extracción de métricas para sistemas modernos (RHEL 7+, Debian, etc.)
    """
    metrics = {}
    
    # CPU: % uso sumando user y system
    cpu_cmd = "top -bn1 | grep 'Cpu(s)' | awk '{print $2 + $4}' | sed 's/,/./'"
    # RAM: % uso
    ram_cmd = "free | grep Mem | awk '{print $3/$2 * 100.0}' | sed 's/,/./'"
    # Disco: % uso de la raíz
    disk_cmd = "df -h / | tail -1 | awk '{print $5}' | sed 's/%//' | sed 's/,/./'"

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

    try:
        val = float(execute_command(client, disk_cmd))
        metrics['Disk_Usage'] = Decimal(str(round(val, 2)))
    except:
        metrics['Disk_Usage'] = Decimal("0.0")

    # Uptime universal
    try:
        val = float(execute_command(client, "awk '{print $1/86400}' /proc/uptime").replace(',', '.'))
        metrics['Uptime'] = Decimal(str(round(val, 2)))
    except:
        metrics['Uptime'] = Decimal("0.0")

    return metrics

def get_metrics_legacy(client) -> dict:
    """
    Extracción de métricas para sistemas antiguos (RHEL 4/5)
    """
    metrics = {}
    
    # CPU: En legacy top -bn1 suele tener el formato diferente
    cpu_cmd = "top -bn1 | grep 'Cpu(s)' | awk '{print $2}' | sed 's/%us,//' | sed 's/,/./'"
    # RAM: free -m es más seguro en legacy
    ram_cmd = "free -m | grep Mem | awk '{print ($3/$2)*100.0}' | sed 's/,/./'"
    # Disco: df -h suele ser compatible
    disk_cmd = "df -h / | tail -1 | awk '{print $5}' | sed 's/%//' | sed 's/,/./'"

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

    try:
        val = float(execute_command(client, disk_cmd))
        metrics['Disk_Usage'] = Decimal(str(round(val, 2)))
    except:
        metrics['Disk_Usage'] = Decimal("0.0")

    try:
        val = float(execute_command(client, "awk '{print $1/86400}' /proc/uptime").replace(',', '.'))
        metrics['Uptime'] = Decimal(str(round(val, 2)))
    except:
        metrics['Uptime'] = Decimal("0.0")

    return metrics
