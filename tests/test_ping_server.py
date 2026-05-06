import urllib.request
import json
import urllib.error
import urllib.parse

# --- VARIABLES CONFIGURABLES ---
BASE_URL = "http://localhost:8000"
ADMIN_EMAIL = "admin@admin.com"
ADMIN_PASS = "123Nokia"
TARGET_IP = "148.215.1.98"
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

# 2. Probar Ping al Servidor
print(f"\nConsultando conectividad (Ping) a: {TARGET_IP}...")
ping_url = f"/servidores/ping/{TARGET_IP}"

# El endpoint devuelve un booleano directamente
ping_res = req(ping_url, "GET", token=token)

if ping_res is True:
    print(f"RESULTADO: El servidor {TARGET_IP} es ALCANZABLE (True).")
elif ping_res is False:
    print(f"RESULTADO: El servidor {TARGET_IP} NO responde (False).")
else:
    print("RESULTADO: No se pudo determinar el estado o hubo un error en la petición.")
