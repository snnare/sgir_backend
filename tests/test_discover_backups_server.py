import urllib.request
import json
import urllib.error
import urllib.parse

# --- VARIABLES CONFIGURABLES ---
BASE_URL = "http://localhost:8000"
ADMIN_EMAIL = "admin@admin.com"
ADMIN_PASS = "123Nokia"

# Datos del Servidor
SERVER_NAME = "SRV-TEST Moderno"
SERVER_IP = "148.215.109.242" # Cambiar por IP real si se desea probar conexión
ES_LEGACY = False

# Datos de la Ruta de Respaldo
BACKUP_PATH = "/bkpbd/Backup/"
RUTA_DESC = "Server No critico"

# Datos de la Credencial SSH
SSH_USER = "areabd"
SSH_PASS = "B@s3#my8s3r!"

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

# 1.1 Test Ping to Server IP
print(f"Probando conectividad (Ping) a {SERVER_IP}...")
ping_payload = {"ip": SERVER_IP}
ping_res = req("/health/ping", "POST", ping_payload, token)
if ping_res is True:
    print(f"Ping exitoso: El servidor {SERVER_IP} es alcanzable.")
else:
    print(f"Ping fallido: El servidor {SERVER_IP} NO responde. Continuando con el registro...")

# 2. Registrar Servidor
print(f"Registrando servidor: {SERVER_NAME} ({SERVER_IP})...")
server_payload = {
    "nombre_servidor": SERVER_NAME,
    "direccion_ip": SERVER_IP,
    "es_legacy": ES_LEGACY,
    "descripcion": "Servidor creado por script de test",
    "id_nivel_criticidad": 1,
    "id_estado_servidor": 1
}
server_res = req("/servidores/", "POST", server_payload, token)
if "id_servidor" in server_res:
    server_id = server_res["id_servidor"]
    print(f"Servidor creado con ID: {server_id}")
else:
    print("Error al crear servidor o ya existe. Intentando obtener por IP...")
    # Intento obtenerlo si ya existe
    all_servers = req("/servidores/", "GET", token=token)
    server_id = next((s["id_servidor"] for s in all_servers if s["direccion_ip"] == SERVER_IP), None)
    if not server_id:
        print("No se pudo obtener el servidor.")
        exit(1)
    print(f"Usando servidor existente con ID: {server_id}")

# 3. Registrar Ruta de Respaldo
print(f"Registrando ruta de respaldo: {BACKUP_PATH}...")
ruta_payload = {
    "descripcion_ruta": RUTA_DESC,
    "path": BACKUP_PATH,
    "id_tipo_almacenamiento": 1, # Local
    "id_estado_ruta": 1 # Activo
}
ruta_res = req("/rutas-respaldo/", "POST", ruta_payload, token)
if "id_ruta" in ruta_res:
    ruta_id = ruta_res["id_ruta"]
    print(f"Ruta creada con ID: {ruta_id}")
else:
    # Si falla, buscamos una existente
    rutas = req("/rutas-respaldo/", "GET", token=token)
    ruta_id = next((r["id_ruta"] for r in rutas if r["path"] == BACKUP_PATH), None)
    if not ruta_id:
        print("Error al crear o encontrar la ruta.")
        exit(1)
    print(f"Usando ruta existente con ID: {ruta_id}")

# 4. Registrar Credencial SSH
print(f"Registrando credencial SSH para usuario: {SSH_USER}...")
cred_payload = {
    "usuario": SSH_USER,
    "password": SSH_PASS,
    "id_tipo_acceso": 1, # SSH
    "id_estado_credencial": 1, # Activo
    "id_servidor": server_id
}
cred_res = req("/credenciales/", "POST", cred_payload, token)
if "id_credencial" in cred_res:
    cred_id = cred_res["id_credencial"]
    print(f"Credencial creada con ID: {cred_id}")
else:
    # Si falla, buscamos una existente para ese servidor
    creds = req(f"/credenciales/servidor/{server_id}", "GET", token=token)
    cred_id = next((c["id_credencial"] for c in creds if c["usuario"] == SSH_USER and c["id_tipo_acceso"] == 1), None)
    if not cred_id:
        print("Error al crear o encontrar la credencial.")
        exit(1)
    print(f"Usando credencial existente con ID: {cred_id}")

# 5. Ejecutar Descubrimiento Global por Servidor
print("\n" + "="*50)
print(f"EJECUTANDO DISCOVERY GLOBAL EN SERVER {server_id}")
print(f"URL: /monitoring/inventory/discover-backups-server/{server_id}/{cred_id}/{ruta_id}")
print("="*50)

final_res = req(f"/monitoring/inventory/discover-backups-server/{server_id}/{cred_id}/{ruta_id}", "POST", payload={}, token=token)
print("Resultado:", json.dumps(final_res, indent=2))
