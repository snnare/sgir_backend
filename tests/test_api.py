import urllib.request
import json
import urllib.error
import urllib.parse

base_url = "http://localhost:8000"

def req(url, method, payload=None, token=None):
    headers = {}
    if payload is not None and not isinstance(payload, bytes):
        payload_bytes = json.dumps(payload).encode()
        headers["Content-Type"] = "application/json"
    else:
        payload_bytes = payload
        
    if token:
        headers["Authorization"] = f"Bearer {token}"
        
    request = urllib.request.Request(f"{base_url}{url}", data=payload_bytes, headers=headers, method=method)
    try:
        resp = urllib.request.urlopen(request)
        read_data = resp.read().decode()
        if read_data:
            return json.loads(read_data)
        return True
    except urllib.error.HTTPError as e:
        print(f"Error en {method} {url}: {e.read().decode()}")
        return None

# 1. Register User
user_data = {
    "nombres": "Admin", "apellidos": "Admin",
    "email": "admin@admin.com", "password": "123Nokia",
    "id_rol": 1, "id_estado_usuario": 1
}
req("/users/", "POST", user_data)

# 2. Login
login_data = urllib.parse.urlencode({"username": "admin@admin.com", "password": "123Nokia"}).encode()
login_req = urllib.request.Request(f"{base_url}/users/login", data=login_data, headers={"Content-Type": "application/x-www-form-urlencoded"}, method="POST")
try:
    token_info = json.loads(urllib.request.urlopen(login_req).read().decode())
    token = token_info["access_token"]
except Exception as e:
    print("Login fallido. Verifica si el usuario existe.")
    exit(1)

# 3. Create Credentials
creds = [
    {"usuario": "sgir", "password": "sgir", "id_tipo_acceso": 2, "id_estado_credencial": 1, "id_servidor": 1},
    {"usuario": "sgir", "password": "sgir", "id_tipo_acceso": 2, "id_estado_credencial": 1, "id_servidor": 2},
    {"usuario": "sgir", "password": "sgir", "id_tipo_acceso": 2, "id_estado_credencial": 1, "id_servidor": 3},
    {"usuario": "SYS", "password": "123Nokia$", "id_tipo_acceso": 2, "id_estado_credencial": 1, "id_servidor": 4},
    {"usuario": "sgir", "password": "sgir", "id_tipo_acceso": 2, "id_estado_credencial": 1, "id_servidor": 5}
]

print("Registrando credenciales...")
for c in creds:
    res = req("/credenciales/", "POST", c, token)
    if res and "id_credencial" in res:
        print("Creada credencial para servidor", c["id_servidor"], "con ID", res["id_credencial"])

# 4. Discover
print("\nProbando Auto-Descubrimiento en /monitoring/inventory/discover/2/2 ...")
discover_res = req("/monitoring/inventory/discover/2/2", "POST", payload={}, token=token)
if discover_res:
    print("Resultado Descubrimiento:", json.dumps(discover_res, indent=2))
