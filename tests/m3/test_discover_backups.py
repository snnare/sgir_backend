import sys
import httpx

# Variables de autenticación al principio del código
BASE_URL = "http://localhost:8000"
ADMIN_EMAIL = "admin@admin.com"
ADMIN_PASSWORD = "123Nokia"

def run_test():
    print("=== INICIANDO PRUEBA DE DESCUBRIMIENTO DE RESPALDOS (MÓDULO 3) ===")
    
    # 1. Crear cliente HTTP
    with httpx.Client(base_url=BASE_URL, timeout=30.0) as client:
        # 2. Login
        print(f"\n[*] Intentando iniciar sesión con {ADMIN_EMAIL}...")
        login_payload = {
            "username": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        }
        try:
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
        
        # 3. Solicitar IP por terminal
        try:
            ip = input("\n[?] Ingrese la IP del servidor a escanear (ej: 148.215.1.90): ").strip()
        except KeyboardInterrupt:
            print("\nOperación cancelada por el usuario.")
            sys.exit(0)
            
        if not ip:
            print("[!] La IP no puede estar vacía.")
            sys.exit(1)
            
        # 4. Obtener información del servidor por IP
        print(f"\n[*] Buscando servidor con IP: {ip}...")
        server_res = client.get(f"/sgir/v1/crud/servidores/ip/{ip}", headers=headers)
        if server_res.status_code != 200:
            print(f"[!] Error al buscar servidor ({server_res.status_code}): {server_res.text}")
            sys.exit(1)
            
        server_data = server_res.json().get("server", {})
        servidor_id = server_data.get("id_servidor")
        nombre_servidor = server_data.get("nombre_servidor")
        print(f"[+] Servidor encontrado: {nombre_servidor} (ID: {servidor_id})")
        
        # 5. Obtener instancias del servidor
        print(f"[*] Obteniendo instancias DBMS para el servidor {nombre_servidor}...")
        instancias_res = client.get(f"/sgir/v1/crud/instancias/servidor/{servidor_id}", headers=headers)
        if instancias_res.status_code != 200:
            print(f"[!] Error al obtener instancias ({instancias_res.status_code}): {instancias_res.text}")
            sys.exit(1)
            
        instancias = instancias_res.json()
        if not instancias:
            print("[!] No se encontraron instancias DBMS asociadas a este servidor.")
            sys.exit(1)
            
        # Seleccionar instancia
        instancia_id = None
        if len(instancias) == 1:
            inst = instancias[0]
            instancia_id = inst["id_instancia"]
            print(f"[+] Seleccionada automáticamente instancia: {inst['nombre_instancia']} (ID: {instancia_id})")
        else:
            print("\nInstancias DBMS disponibles:")
            for idx, inst in enumerate(instancias, 1):
                print(f"  {idx}. {inst['nombre_instancia']} (Puerto: {inst['puerto']}, ID: {inst['id_instancia']})")
            try:
                sel = input(f"[?] Seleccione el número de la instancia (1-{len(instancias)}) [1]: ").strip()
                sel_idx = int(sel) if sel else 1
                inst = instancias[sel_idx - 1]
                instancia_id = inst["id_instancia"]
            except (ValueError, IndexError):
                print("[!] Selección inválida.")
                sys.exit(1)
                
        # 6. Obtener credenciales SSH del servidor
        print(f"\n[*] Obteniendo credenciales del servidor...")
        credenciales_res = client.get(f"/sgir/v1/crud/credenciales/servidor/{servidor_id}", headers=headers)
        if credenciales_res.status_code != 200:
            print(f"[!] Error al obtener credenciales ({credenciales_res.status_code}): {credenciales_res.text}")
            sys.exit(1)
            
        credenciales = credenciales_res.json()
        # Intentamos filtrar las SSH (id_tipo_acceso == 1)
        credenciales_ssh = []
        for c in credenciales:
            tipo_id = None
            if isinstance(c.get("tipo"), dict):
                tipo_id = c["tipo"].get("id_tipo_acceso")
            elif c.get("id_tipo_acceso") is not None:
                tipo_id = c["id_tipo_acceso"]
                
            if tipo_id == 1:
                credenciales_ssh.append(c)
                
        if not credenciales_ssh:
            # Fallback a usar todas las credenciales si por alguna razón no se filtró nada
            credenciales_ssh = credenciales
            
        if not credenciales_ssh:
            print("[!] No se encontraron credenciales SSH asociadas a este servidor.")
            sys.exit(1)
            
        # Seleccionar credencial
        credencial_id = None
        if len(credenciales_ssh) == 1:
            cred = credenciales_ssh[0]
            credencial_id = cred["id_credencial"]
            print(f"[+] Seleccionada automáticamente credencial: {cred['usuario']} (ID: {credencial_id})")
        else:
            print("\nCredenciales SSH disponibles:")
            for idx, cred in enumerate(credenciales_ssh, 1):
                tipo_nombre = cred.get("tipo", {}).get("nombre_tipo", "SSH") if isinstance(cred.get("tipo"), dict) else "SSH"
                print(f"  {idx}. Usuario: {cred['usuario']} (Tipo: {tipo_nombre}, ID: {cred['id_credencial']})")
            try:
                sel = input(f"[?] Seleccione el número de la credencial (1-{len(credenciales_ssh)}) [1]: ").strip()
                sel_idx = int(sel) if sel else 1
                cred = credenciales_ssh[sel_idx - 1]
                credencial_id = cred["id_credencial"]
            except (ValueError, IndexError):
                print("[!] Selección inválida.")
                sys.exit(1)
                
        # 7. Obtener rutas de respaldo del servidor
        print(f"\n[*] Obteniendo rutas de respaldo del servidor...")
        rutas_res = client.get(f"/sgir/v1/crud/rutas-respaldo/servidor/{servidor_id}", headers=headers)
        if rutas_res.status_code != 200:
            print(f"[!] Error al obtener rutas de respaldo ({rutas_res.status_code}): {rutas_res.text}")
            sys.exit(1)
            
        rutas = rutas_res.json()
        if not rutas:
            print("[!] No se encontraron rutas de respaldo asociadas a este servidor.")
            sys.exit(1)
            
        # Seleccionar ruta
        ruta_id = None
        if len(rutas) == 1:
            r = rutas[0]
            ruta_id = r["id_ruta"]
            print(f"[+] Seleccionada automáticamente ruta: {r['path']} (ID: {ruta_id})")
        else:
            print("\nRutas de respaldo disponibles:")
            for idx, r in enumerate(rutas, 1):
                print(f"  {idx}. Path: {r['path']} (ID: {r['id_ruta']})")
            try:
                sel = input(f"[?] Seleccione el número de la ruta (1-{len(rutas)}) [1]: ").strip()
                sel_idx = int(sel) if sel else 1
                r = rutas[sel_idx - 1]
                ruta_id = r["id_ruta"]
            except (ValueError, IndexError):
                print("[!] Selección inválida.")
                sys.exit(1)
                
        # 8. Ejecutar el endpoint de descubrimiento de respaldos
        endpoint_path = f"/sgir/v1/m3/inventory/discover-backups/{instancia_id}/{credencial_id}/{ruta_id}"
        print(f"\n[*] Ejecutando POST a {endpoint_path}...")
        
        discover_res = client.post(endpoint_path, headers=headers)
        
        print(f"\n[=] Respuesta HTTP {discover_res.status_code}:")
        if discover_res.status_code == 200:
            print("[+] ¡Éxito! Resultados obtenidos:")
            import json
            print(json.dumps(discover_res.json(), indent=2, ensure_ascii=False))
        else:
            print(f"[!] Error ejecutando descubrimiento: {discover_res.text}")

if __name__ == "__main__":
    try:
        run_test()
    except Exception as e:
        print(f"[!] Error inesperado: {str(e)}")
        sys.exit(1)
