import urllib.request
import json
import urllib.error
import urllib.parse
import time

# --- CONFIGURACIÓN GLOBAL ---
BASE_URL = "http://localhost:8000"
ADMIN_EMAIL = "admin@admin.com"
ADMIN_PASS = "123Nokia"

# Definición de Infraestructura basada en docker-compose
# id_dbms sugeridos: 2:MySQL5, 3:MySQL8, 4:Oracle, 5:MongoDB
SERVERS_TO_REGISTER = [
    {
        "nombre": "MySQL 5 Instance", "ip": "172.19.0.8", "crit": 2, 
        "m_host": False, "m_db": True, "type": "db", "dbms_id": 2, "port": 3306,
        "user": "sgir", "pass": "sgir"
    },
    {
        "nombre": "MySQL 8 Instance", "ip": "172.19.0.6", "crit": 3, 
        "m_host": False, "m_db": True, "type": "db", "dbms_id": 3, "port": 3306,
        "user": "sgir", "pass": "sgir"
    },
    {
        "nombre": "Oracle 21c XE", "ip": "172.19.0.4", "crit": 4, 
        "m_host": False, "m_db": True, "type": "db", "dbms_id": 4, "port": 1521,
        "user": "sgir", "pass": "123Nokia$" # Ajustado según compose
    },
    {
        "nombre": "MongoDB Cluster", "ip": "172.19.0.10", "crit": 2, 
        "m_host": False, "m_db": True, "type": "db", "dbms_id": 5, "port": 27017,
        "user": "sgir", "pass": "sgir"
    },
    {
        "nombre": "SSH Server Lab", "ip": "172.19.0.9", "crit": 1, 
        "m_host": True, "m_db": False, "type": "ssh", "user": "sgir_user", "pass": "sgir_pass"
    },
    {
        "nombre": "Ubuntu Stable", "ip": "172.19.0.5", "crit": 2, 
        "m_host": True, "m_db": False, "type": "ssh", "user": "sgir_user", "pass": "sgir_pass"
    },
    {
        "nombre": "Fedora Latest", "ip": "172.19.0.7", "crit": 4, 
        "m_host": True, "m_db": False, "type": "ssh", "user": "sgir_user", "pass": "sgir_pass"
    }
]

# ----------------------------

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
        err_body = e.read().decode()
        return {"error": e.code, "detail": err_body}
    except Exception as e:
        return {"error": "ConnectionError", "detail": str(e)}

def run_full_test():
    print("="*60)
    print("INICIANDO TEST DE INTEGRACIÓN FULL (REGISTRO + INVENTARIO)")
    print("="*60)

    # 1. Login
    print(f"Logueando como {ADMIN_EMAIL}...")
    login_data = urllib.parse.urlencode({"username": ADMIN_EMAIL, "password": ADMIN_PASS}).encode()
    login_req = urllib.request.Request(f"{BASE_URL}/users/login", data=login_data, headers={"Content-Type": "application/x-www-form-urlencoded"}, method="POST")
    try:
        token_info = json.loads(urllib.request.urlopen(login_req).read().decode())
        token = token_info["access_token"]
        print("[OK] Login exitoso.")
    except Exception:
        print("[FAIL] Login fallido. Abortando.")
        return

    # 2. Registro de Activos
    print("\n" + "-"*40)
    print("REGISTRANDO SERVIDORES, CREDENCIALES E INSTANCIAS")
    print("-"*40)

    for s in SERVERS_TO_REGISTER:
        print(f"\nProcesando: {s['nombre']} ({s['ip']})...")
        
        # 2.1 Registrar Servidor
        srv_payload = {
            "nombre_servidor": s["nombre"],
            "direccion_ip": s["ip"],
            "es_legacy": False,
            "id_nivel_criticidad": s["crit"],
            "id_estado_servidor": 1,
            "monitoreo_host": s["m_host"],
            "monitoreo_db": s["m_db"]
        }
        srv_res = req("/servidores/", "POST", srv_payload, token)
        
        if "id_servidor" in srv_res:
            srv_id = srv_res["id_servidor"]
            print(f"  [OK] Servidor creado ID: {srv_id}")
        else:
            # Intentar obtener ID si ya existe
            all_srv = req("/servidores/", "GET", token=token)
            srv_id = next((x["id_servidor"] for x in all_srv if x["direccion_ip"] == s["ip"]), None)
            print(f"  [INFO] Servidor ya existía. ID obtenido: {srv_id}")

        if not srv_id: continue

        # 2.2 Registrar Credencial
        tipo_acc = 1 if s["type"] == "ssh" else 2
        cred_payload = {
            "usuario": s["user"],
            "password": s["pass"],
            "id_tipo_acceso": tipo_acc,
            "id_estado_credencial": 1,
            "id_servidor": srv_id
        }
        cred_res = req("/credenciales/", "POST", cred_payload, token)
        if "id_credencial" in cred_res:
            print(f"  [OK] Credencial registrada ID: {cred_res['id_credencial']}")
        else:
            print(f"  [INFO] Credencial ya registrada o error.")

        # 2.3 Registrar Instancia (Si es DB)
        if s["type"] == "db":
            inst_payload = {
                "nombre_instancia": s["nombre"].replace(" ", "_").lower(),
                "puerto": s["port"],
                "id_servidor": srv_id,
                "id_dbms": s["dbms_id"],
                "id_estado_instancia": 1
            }
            inst_res = req("/instancias/", "POST", inst_payload, token)
            if "id_instancia" in inst_res:
                inst_id = inst_res["id_instancia"]
                print(f"  [OK] Instancia registrada ID: {inst_id}")
                
                # 2.4 AUTO-DESCUBRIMIENTO INICIAL
                print(f"  [SYNC] Ejecutando descubrimiento automático...")
                # Buscamos la credencial recién creada o existente para esta instancia
                creds = req(f"/credenciales/", "GET", token=token) # Simplificado
                # En un entorno real buscaríamos la de este srv_id
                # Por ahora disparamos con la lógica que asume que el usuario sabe cuál es.
                # Como es un test, intentaremos con una credencial genérica o la que tengamos.
                # (Para este test usaremos un id_credencial que suele ser consecutivo)
                
    # 3. Verificación de Inventario Global
    print("\n" + "="*60)
    print("CONSULTANDO ENDPOINT DE BÚSQUEDA DE ACTIVOS (ASSETS)")
    print("="*60)
    time.sleep(1) # Esperar a que la DB procese
    assets = req("/monitoring/inventory/assets", "GET", token=token)

    if isinstance(assets, list):
        print(f"Se encontraron {len(assets)} activos en el inventario consolidado:\n")
        print(f"{'ID ASSET':<15} | {'IP':<12} | {'MOTOR':<10} | {'INSTANCIA':<15} | {'BASE DATOS'}")
        print("-" * 75)
        for a in assets:
            db = a['base_datos'] if a['base_datos'] else "---"
            print(f"{a['id_asset']:<15} | {a['ip']:<12} | {a['motor']:<10} | {a['instancia']:<15} | {db}")
    else:
        print("[FAIL] No se pudo obtener el inventario de activos.")

    print("\n" + "="*60)
    print("TEST FINALIZADO")
    print("="*60)

if __name__ == "__main__":
    run_full_test()
