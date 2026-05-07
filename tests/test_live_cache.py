import urllib.request
import json
import urllib.error
import urllib.parse
from datetime import datetime

# --- VARIABLES CONFIGURABLES ---
BASE_URL = "http://localhost:8000"
ADMIN_EMAIL = "admin@admin.com"
ADMIN_PASS = "123Nokia"
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
        return None

# 1. Login
print(f"Iniciando sesión como {ADMIN_EMAIL}...")
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

# 2. Consultar Live Cache
print("\n" + "="*80)
print("CONSULTANDO MÉTRICAS EN TIEMPO REAL (LIVE CACHE)")
print("="*80)

live_data = req("/monitoring/host/live-cache", "GET", token=token)

if not live_data:
    print("La caché está vacía. Asegúrate de que el Scheduler esté encendido y haya realizado al menos un ciclo.")
else:
    print(f"{'ID SRV':<8} | {'CPU %':<8} | {'RAM %':<8} | {'DISCOS (Path: % Use)':<40} | {'ÚLTIMA ACTUALIZACIÓN'}")
    print("-" * 110)
    
    for server_id, metrics in live_data.items():
        # Soporte para formato compacto: "cpu|ram|disks|uptime|timestamp"
        if isinstance(metrics, str):
            parts = metrics.split("|")
            cpu = float(parts[0])
            ram = float(parts[1])
            disks_str = parts[2]
            uptime = float(parts[3])
            # Convertir timestamp unix a legible
            last_update = datetime.fromtimestamp(int(parts[4])).strftime('%Y-%m-%d %H:%M:%S')
        else:
            # Formato antiguo (Legacy)
            cpu = metrics.get("cpu", 0)
            ram = metrics.get("ram", 0)
            uptime = metrics.get("uptime", 0)
            last_update = metrics.get("last_update", "N/A")
            disks = metrics.get("disks", {})
            disks_str = " | ".join([f"{path}: {pct}%" for path, pct in disks.items()])
        
        print(f"{server_id:<8} | {cpu:<8.1f} | {ram:<8.1f} | {disks_str:<40} | {last_update}")

print("\n" + "="*80)
print("Fin de la consulta.")
