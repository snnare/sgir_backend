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

# 1. Register User (if not exists)
print("Registrando usuario admin...")
user_data = {
    "nombres": "Admin", 
    "apellidos": "Admin",
    "email": "admin@admin.com", 
    "password": "123Nokia",
    "id_rol": 1, 
    "id_estado_usuario": 1
}
req("/users/", "POST", user_data)

# 2. Login
print("Iniciando sesión...")
login_data = urllib.parse.urlencode({"username": "admin@admin.com", "password": "123Nokia"}).encode()
login_req = urllib.request.Request(
    f"{base_url}/users/login", 
    data=login_data, 
    headers={"Content-Type": "application/x-www-form-urlencoded"}, 
    method="POST"
)
try:
    token_info = json.loads(urllib.request.urlopen(login_req).read().decode())
    token = token_info["access_token"]
    print("Login exitoso.")
except Exception as e:
    print("Login fallido. Verifica si el usuario existe.")
    exit(1)

# 3. Filter by IP
target_ip = "192.168.1.10"
print(f"\nFiltrando bases de datos por IP: {target_ip}...")

# El endpoint es GET /bases-de-datos/filter?ip={target_ip}
query_params = urllib.parse.urlencode({"ip": target_ip})
filter_url = f"/bases-de-datos/filter?{query_params}"

filter_res = req(filter_url, "GET", token=token)

if filter_res is not None:
    print(f"Resultado de filtro para IP '{target_ip}':")
    print(json.dumps(filter_res, indent=2))
else:
    print("No se obtuvieron resultados o hubo un error en el filtrado.")

# 4. Filter by Name and IP
target_name = "prod"
print(f"\nFiltrando por Nombre: '{target_name}' e IP: '{target_ip}'...")
query_params_combined = urllib.parse.urlencode({"nombre": target_name, "ip": target_ip})
filter_combined_url = f"/bases-de-datos/filter?{query_params_combined}"

filter_combined_res = req(filter_combined_url, "GET", token=token)

if filter_combined_res is not None:
    print(f"Resultado de filtro combinado:")
    print(json.dumps(filter_combined_res, indent=2))
