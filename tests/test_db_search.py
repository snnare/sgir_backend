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

# 3. Dynamic Search for Database
db_name_query = "sgir_db_5"
print(f"\nBuscando base de datos: {db_name_query}...")

# El endpoint es GET /bases-de-datos/search?query={db_name_query}
query_params = urllib.parse.urlencode({"query": db_name_query})
search_url = f"/bases-de-datos/search?{query_params}"

search_res = req(search_url, "GET", token=token)

if search_res is not None:
    print(f"Resultado de búsqueda para '{db_name_query}':")
    print(json.dumps(search_res, indent=2))
else:
    print("No se obtuvieron resultados o hubo un error en la búsqueda.")
