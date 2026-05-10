import urllib.request
import json
import urllib.error
import urllib.parse
from datetime import datetime, timedelta

# --- CONFIGURACIÓN ---
BASE_URL = "http://localhost:8000"
ADMIN_EMAIL = "admin@admin.com"
ADMIN_PASS = "123Nokia"

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
        print(f"Error {e.code}: {err_body}")
        return {"error": e.code, "detail": err_body}

def test_retention_manager():
    print("="*60)
    print("TEST DE RETENTION MANAGER (EXPIRACIÓN DE RESPALDOS)")
    print("="*60)

    # 1. Login
    login_data = urllib.parse.urlencode({"username": ADMIN_EMAIL, "password": ADMIN_PASS}).encode()
    login_req = urllib.request.Request(f"{BASE_URL}/users/login", data=login_data, headers={"Content-Type": "application/x-www-form-urlencoded"}, method="POST")
    token_info = json.loads(urllib.request.urlopen(login_req).read().decode())
    token = token_info["access_token"]

    # 2. Crear una Política de Prueba (Retención: 0 días para forzar expiración inmediata)
    print("\n1. Creando política de retención inmediata (0 días)...")
    politica_payload = {
        "nombre_politica": "Test Retention 0",
        "descripcion": "Política para pruebas de expiración",
        "frecuencia_horas": 24,
        "retencion_dias": 0,
        "id_tipo_respaldo": 1,
        "id_estado_politica": 1
    }
    pol_res = req("/politicas-respaldo/", "POST", politica_payload, token)
    pol_id = pol_res["id_politica"]
    print(f"   [OK] Política creada ID: {pol_id}")

    # 3. Crear un registro de respaldo "viviendo" en esa política
    print("\n2. Creando registro de respaldo (Simulando ejecución exitosa)...")
    respaldo_payload = {
        "fecha_inicio": (datetime.now() - timedelta(hours=1)).isoformat(), # Hace 1 hora
        "fecha_fin": datetime.now().isoformat(),
        "tamano_mb": 100.5,
        "hash_integridad": "abc123test",
        "id_base_datos": 1, 
        "id_politica": pol_id,
        "id_credencial": 1,
        "id_ruta_respaldo": 1,
        "id_estado_ejecucion": 4 # Éxito (Asumido)
    }
    # Nota: Si el endpoint no existe, usaremos el servicio directamente o crearemos el endpoint
    res_res = req("/respaldos/", "POST", respaldo_payload, token)
    res_id = res_res["id_respaldo"]
    print(f"   [OK] Respaldo registrado ID: {res_id} | Estado inicial: 4")

    # 4. Trigger de la tarea de retención
    print("\n3. Disparando manualmente la política de retención vía API...")
    trigger_res = req("/monitoring/scheduler/trigger-backup-retention", "POST", payload={}, token=token)
    print(f"   [OK] Respuesta del API: {trigger_res.get('message')}")

    # 5. Verificar cambio de estado
    print("\n4. Verificando cambio de estado en la base de datos...")
    # Consultamos el historial para ver el estado actual del respaldo
    historial = req(f"/respaldos/historial?id_base_datos=1", "GET", token=token)
    
    # Buscamos nuestro respaldo específico
    res_actualizado = next((r for r in historial if r["id_respaldo"] == res_id), None)
    
    if res_actualizado:
        # Debemos saber cuál es el ID del estado 'Expirado'
        # El script retention_manager lo crea si no existe. 
        # Vamos a imprimir el nombre del estado si el response lo trae o el ID.
        print(f"   [INFO] Estado final del respaldo {res_id}: {res_actualizado['id_estado_ejecucion']}")
        # Nota: RespaldoResponse usa el ID del estado.
    else:
        print("   [FAIL] No se encontró el respaldo en el historial.")

if __name__ == "__main__":
    test_retention_manager()
