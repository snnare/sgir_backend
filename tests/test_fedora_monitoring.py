import urllib.request
import json
import urllib.error
import urllib.parse
import time
from datetime import datetime

# --- VARIABLES CONFIGURABLES ---
BASE_URL = "http://localhost:8000"
ADMIN_EMAIL = "admin@admin.com"
ADMIN_PASS = "123Nokia"

# Datos del Servidor (Fedora Latest)
SERVER_NAME = "Fedora Latest"
SERVER_IP = "148.215.1.98" 
ES_LEGACY = True
CRITICIDAD_CRITICA = 4 # Misión Crítica

# Datos de la Credencial SSH
SSH_USER = "sgir_user"
SSH_PASS = "sgir_pass"

# -------------------------------

def req(url, method, payload=None, token=None):
    headers = {}
    if payload is not None and not isinstance(payload, bytes):
        payload_bytes = json.dumps(payload).encode()
        headers["Content-Type"] = "application/json"
    else:
        payload_bytes = payload
        
    if token:
        headers["Authorization"] = f"Bearer {token}"
        
    request = urllib.request.Request(f"{BASE_URL}{url}", data=payload_bytes, headers=headers, method=method)
    try:
        resp = urllib.request.urlopen(request)
        read_data = resp.read().decode()
        if read_data:
            return json.loads(read_data)
        return True
    except urllib.error.HTTPError as e:
        error_msg = e.read().decode()
        print(f"Error en {method} {url}: {error_msg}")
        return {"error": error_msg}

# 1. Login
print("Iniciando sesión...")
login_data = urllib.parse.urlencode({"username": ADMIN_EMAIL, "password": ADMIN_PASS}).encode()
login_req = urllib.request.Request(
    f"{BASE_URL}/users/login", 
    data=login_data, 
    headers={"Content-Type": "application/x-www-form-urlencoded"}, 
    method="POST"
)
try:
    token_info = json.loads(urllib.request.urlopen(login_req).read().decode())
    token = token_info["access_token"]
    print("Login exitoso.")
except Exception as e:
    print(f"Login fallido. Asegúrate de que el usuario {ADMIN_EMAIL} exista.")
    exit(1)

# 2. Registrar Servidor con Criticidad CRÍTICA
print(f"Registrando servidor: {SERVER_NAME} con criticidad CRÍTICA...")
server_payload = {
    "nombre_servidor": SERVER_NAME,
    "direccion_ip": SERVER_IP,
    "es_legacy": ES_LEGACY,
    "descripcion": "Servidor Fedora Crítico para test de scheduler",
    "id_nivel_criticidad": CRITICIDAD_CRITICA,
    "id_estado_servidor": 1
}
server_res = req("/servidores/", "POST", server_payload, token)
if isinstance(server_res, dict) and "id_servidor" in server_res:
    server_id = server_res["id_servidor"]
    print(f"Servidor creado con ID: {server_id}")
else:
    all_servers = req("/servidores/", "GET", token=token)
    server_id = next((s["id_servidor"] for s in all_servers if s["direccion_ip"] == SERVER_IP), None)
    if not server_id:
        print("Error al obtener servidor.")
        exit(1)
    # Actualizar criticidad por si acaso era diferente
    req(f"/servidores/{server_id}", "PUT", {"id_nivel_criticidad": CRITICIDAD_CRITICA}, token)
    print(f"Usando servidor existente con ID: {server_id} (Criticidad actualizada a 4)")

# 3. Registrar Credencial SSH
print(f"Registrando credencial SSH...")
cred_payload = {
    "usuario": SSH_USER,
    "password": SSH_PASS,
    "id_tipo_acceso": 1,
    "id_estado_credencial": 1,
    "id_servidor": server_id
}
cred_res = req("/credenciales/", "POST", cred_payload, token)

# 4. Activar en tabla Monitoreo (Whitelist para el Scheduler)
print(f"Activando servidor {server_id} en la lista de monitoreo...")
req("/monitoreo/", "POST", {"id_servidor": server_id, "id_estado_monitoreo": 1}, token)

# 5. Iniciar Scheduler
print("Reanudando APScheduler...")
req("/monitoring/host/scheduler/resume", "POST", token=token)

# 6. Escuchar métricas durante 60 segundos
print("\n" + "="*60)
print(f"ESCUCHANDO MÉTRICAS DE {SERVER_NAME} DURANTE 1 MINUTO")
print(f"IP: {SERVER_IP} | Criticidad: {CRITICIDAD_CRITICA}")
print("="*60)

start_time = time.time()
metrics_captured = 0
duration = 60

while time.time() - start_time < duration:
    elapsed = int(time.time() - start_time)
    remaining = duration - elapsed
    summary = req("/monitoring/host/live-cache", "GET", token=token)
    
    # Buscar el servidor en el Live Cache
    if isinstance(summary, dict) and str(server_id) in summary:
        data = summary[str(server_id)]
        metrics_captured += 1
        
        # Soporte para formato compacto: "cpu|ram|disks|uptime|timestamp"
        if isinstance(data, str):
            parts = data.split("|")
            cpu = parts[0]
            ram = parts[1]
            disks = parts[2]
            uptime = parts[3]
            print(f"[{datetime.now().strftime('%H:%M:%S')}] [OK] (COMPACT) CPU: {cpu}% | RAM: {ram}% | DISCOS: {disks} | Uptime: {uptime}s (Quedan {remaining}s)")
        else:
            # Formato antiguo (Legacy)
            print(f"[{datetime.now().strftime('%H:%M:%S')}] [OK] CPU: {data['cpu']}% | RAM: {data['ram']}% | DISCOS: {data['disks']} | Uptime: {data['uptime']}s (Quedan {remaining}s)")
    else:
        print(f"[{datetime.now().strftime('%H:%M:%S')}] [WAIT] Esperando primer latido del scheduler... (Quedan {remaining}s)")
    
    time.sleep(10)

print("\n" + "="*60)
print("TEST FINALIZADO")
print(f"Métricas capturadas: {metrics_captured}")
print("="*60)

# 7. Verificar estado de la sesión en la base de datos
print("\nVerificando última sesión en tabla Monitoreo...")
sessions = req(f"/monitoreo/{server_id}", "GET", token=token) # Nota: esto asume un endpoint que busque por server_id o similar
# Si no hay endpoint por server_id, lo dejamos como opcional o informativo
print("Fin del reporte.")
