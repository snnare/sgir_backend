import urllib.request
import json
import urllib.error
import urllib.parse

# --- VARIABLES CONFIGURABLES ---
BASE_URL = "http://localhost:8000"
ADMIN_EMAIL = "admin@admin.com"
ADMIN_PASS = "123Nokia"

# IDs para probar descubrimiento (Asegúrate de que existan en tu DB o cámbialos)
# Según catálogo DBMS: 2:MySQL5, 3:MySQL8, 4:Oracle, 5:MongoDB
# Usaremos MySQL 8 para este test (ID 3 en DBMS)
TEST_INSTANCIA_ID = 2  # Cambiar según lo que tengas en tu DB local
TEST_CREDENCIAL_ID = 2 
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

# 2. Probar Auto-Descubrimiento (Oracle/Mongo/MySQL)
print("\n" + "="*60)
print(f"PROBANDO AUTO-DESCUBRIMIENTO (Instancia ID: {TEST_INSTANCIA_ID})")
print("="*60)
discovery_res = req(f"/monitoring/inventory/discover/{TEST_INSTANCIA_ID}/{TEST_CREDENCIAL_ID}", "POST", payload={}, token=token)
print("Resultado:", json.dumps(discovery_res, indent=2))

# 3. Consultar Inventario Global (Búsqueda de Activos)
print("\n" + "="*60)
print("CONSULTANDO BÚSQUEDA DE ACTIVOS (INVENTARIO GLOBAL)")
print("="*60)
assets = req("/monitoring/inventory/assets", "GET", token=token)

if isinstance(assets, list):
    print(f"Se encontraron {len(assets)} activos registrados.\n")
    print(f"{'ID ASSET':<20} | {'SERVIDOR':<15} | {'MOTOR':<12} | {'BASE DATOS':<20} | {'ESTADO'}")
    print("-" * 85)
    for asset in assets:
        db_name = asset['base_datos'] if asset['base_datos'] else "---"
        print(f"{asset['id_asset']:<20} | {asset['servidor']:<15} | {asset['motor']:<12} | {db_name:<20} | {asset['estado']}")
else:
    print("Error al obtener los activos.")

print("\n" + "="*60)
print("FIN DEL TEST")
print("="*60)
