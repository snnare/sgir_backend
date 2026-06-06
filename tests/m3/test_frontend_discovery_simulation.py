import sys
import httpx
import json

BASE_URL = "http://localhost:8000"
# Se utilizan las credenciales solicitadas por el usuario, con fallback si es necesario
ADMIN_EMAIL = "amdin@admin.com"
ADMIN_PASSWORD = "123Nokia"
ALT_EMAIL = "admin@admin.com"

def run_simulation():
    print("=====================================================================")
    print("=== SIMULADOR DE FRONTEND: BÚSQUEDA Y AUTO-BÚSQUEDA DE RESPALDOS ===")
    print("=====================================================================\n")
    
    with httpx.Client(base_url=BASE_URL, timeout=45.0) as client:
        # 1. Login
        print(f"[*] Intentando iniciar sesión con {ADMIN_EMAIL}...")
        login_payload = {
            "username": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        }
        try:
            login_response = client.post("/sgir/v1/crud/users/login", data=login_payload)
            # Fallback en caso de que amdin@admin.com no esté en la base (typo común)
            if login_response.status_code != 200:
                print(f"[-] Login falló con {ADMIN_EMAIL}, reintentando con fallback {ALT_EMAIL}...")
                login_payload["username"] = ALT_EMAIL
                login_response = client.post("/sgir/v1/crud/users/login", data=login_payload)
                
            if login_response.status_code != 200:
                print(f"[!] Error de autenticación ({login_response.status_code}): {login_response.text}")
                sys.exit(1)
        except Exception as e:
            print(f"[!] Error de conexión al backend: {str(e)}")
            sys.exit(1)
            
        token_data = login_response.json()
        token = token_data["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        print("[+] Autenticación exitosa.")
        
        # 2. Solicitar IP del Servidor
        try:
            ip = input("\n[?] Ingrese la IP del servidor a escanear (ej: 148.215.1.98): ").strip()
        except KeyboardInterrupt:
            print("\nSimulación cancelada.")
            sys.exit(0)
            
        if not ip:
            print("[!] La IP no puede estar vacía.")
            sys.exit(1)
            
        # 3. Obtener información del servidor en la CMDB
        print(f"\n[*] Buscando servidor con IP: {ip}...")
        server_res = client.get(f"/sgir/v1/crud/servidores/ip/{ip}", headers=headers)
        if server_res.status_code != 200:
            print(f"[!] Error al buscar servidor ({server_res.status_code}): {server_res.text}")
            sys.exit(1)
            
        server_data = server_res.json().get("server", {})
        servidor_id = server_data.get("id_servidor")
        nombre_servidor = server_data.get("nombre_servidor")
        print(f"[+] Servidor encontrado: {nombre_servidor} (ID: {servidor_id})")
        
        # 4. Obtener credenciales SSH
        print(f"[*] Obteniendo credenciales SSH para {nombre_servidor}...")
        credenciales_res = client.get(f"/sgir/v1/crud/credenciales/servidor/{servidor_id}", headers=headers)
        if credenciales_res.status_code != 200:
            print(f"[!] Error al obtener credenciales ({credenciales_res.status_code})")
            sys.exit(1)
            
        credenciales = credenciales_res.json()
        credenciales_ssh = [c for c in credenciales if c.get("id_tipo_acceso") == 1 or (isinstance(c.get("tipo"), dict) and c["tipo"].get("id_tipo_acceso") == 1)]
        if not credenciales_ssh:
            print("[!] No se encontraron credenciales SSH para este servidor.")
            sys.exit(1)
        cred = credenciales_ssh[0]
        credencial_id = cred["id_credencial"]
        print(f"[+] Credencial SSH seleccionada: {cred['usuario']} (ID: {credencial_id})")
        
        # 5. Obtener rutas de respaldo
        print(f"[*] Obteniendo rutas de respaldo asociadas al servidor...")
        rutas_res = client.get(f"/sgir/v1/crud/rutas-respaldo/servidor/{servidor_id}", headers=headers)
        if rutas_res.status_code != 200:
            print(f"[!] Error al obtener rutas de respaldo ({rutas_res.status_code})")
            sys.exit(1)
            
        rutas = rutas_res.json()
        if not rutas:
            print("[!] No se encontraron rutas de respaldo registradas para este servidor.")
            sys.exit(1)
        r = rutas[0]
        ruta_id = r["id_ruta"]
        print(f"[+] Ruta de respaldo seleccionada: {r['path']} (ID: {ruta_id})")
        
        # 6. Seleccionar tipo de escaneo (Simulando el Frontend)
        print("\nSeleccione el tipo de escaneo a simular:")
        print("  1. Escaneo Diario / Rápido (Servidor - Últimas 24h, sin recursividad)")
        print("  2. Escaneo en Caliente / Personalizado (Servidor - Parámetros customizados)")
        print("  3. Escaneo por Instancia (Original - Búsqueda en todos los archivos de la instancia)")
        
        try:
            opcion = input("\n[?] Ingrese el número de opción (1-3) [1]: ").strip() or "1"
        except KeyboardInterrupt:
            print("\nSimulación cancelada.")
            sys.exit(0)
            
        if opcion == "1":
            # POST /m3/inventory/discover-backups-server/{servidor_id}/{credencial_id}/{ruta_id}
            endpoint = f"/sgir/v1/m3/inventory/discover-backups-server/{servidor_id}/{credencial_id}/{ruta_id}"
            print(f"\n[*] Simulando Frontend (Escaneo Diario) -> POST {endpoint}")
            res = client.post(endpoint, headers=headers)
            
        elif opcion == "2":
            # POST /m3/inventory/discover-backups-custom/{servidor_id}/{credencial_id}/{ruta_id}
            try:
                days = input("[?] Días de antigüedad a buscar (0 = todos, default=0): ").strip() or "0"
                deep_input = input("[?] ¿Búsqueda profunda / recursiva? (s/n, default=s): ").strip().lower() or "s"
                deep = "true" if deep_input in ["s", "si", "yes", "true"] else "false"
            except KeyboardInterrupt:
                print("\nSimulación cancelada.")
                sys.exit(0)
                
            endpoint = f"/sgir/v1/m3/inventory/discover-backups-custom/{servidor_id}/{credencial_id}/{ruta_id}?days={days}&deep={deep}"
            print(f"\n[*] Simulando Frontend (Escaneo en Caliente) -> POST {endpoint}")
            res = client.post(endpoint, headers=headers)
            
        elif opcion == "3":
            # Obtener instancias para poder pedir el ID de instancia
            instancias_res = client.get(f"/sgir/v1/crud/instancias/servidor/{servidor_id}", headers=headers)
            instancias = instancias_res.json()
            if not instancias:
                print("[!] No se encontraron instancias DBMS asociadas al servidor.")
                sys.exit(1)
            instancia_id = instancias[0]["id_instancia"]
            
            # POST /m3/inventory/discover-backups/{instancia_id}/{credencial_id}/{ruta_id}
            endpoint = f"/sgir/v1/m3/inventory/discover-backups/{instancia_id}/{credencial_id}/{ruta_id}"
            print(f"\n[*] Simulando Frontend (Escaneo por Instancia) -> POST {endpoint}")
            res = client.post(endpoint, headers=headers)
            
        else:
            print("[!] Opción inválida.")
            sys.exit(1)
            
        # 7. Mostrar resultados
        print(f"\n[=] Respuesta recibida (HTTP {res.status_code}):")
        try:
            print(json.dumps(res.json(), indent=2, ensure_ascii=False))
        except Exception:
            print(res.text)

if __name__ == "__main__":
    try:
        run_simulation()
    except Exception as e:
        print(f"\n[!] Error inesperado en la simulación: {str(e)}")
        sys.exit(1)
