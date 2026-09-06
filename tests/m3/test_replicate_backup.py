import sys
import httpx
import json

# Parámetros de prueba
BASE_URL = "http://localhost:8000"
ADMIN_EMAIL = "admin@admin.com"
ADMIN_PASSWORD = "123Nokia"
SERVER_IP = "148.215.1.98"

def run_test():
    print("=== INICIANDO TEST DE WORKFLOW DE DESCUBRIMIENTO Y REPLICACIÓN SFTP ===")
    
    with httpx.Client(base_url=BASE_URL, timeout=45.0) as client:
        # 1. Login
        print(f"\n[*] Iniciando sesión con {ADMIN_EMAIL}...")
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
            print(f"[!] Error de conexión al backend central: {str(e)}")
            sys.exit(1)
            
        token_data = login_response.json()
        token = token_data["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        print("[+] Login exitoso.")

        # 2. Obtener información del servidor legado por su IP
        print(f"\n[*] Buscando servidor registrado con IP: {SERVER_IP}...")
        server_res = client.get(f"/sgir/v1/crud/servidores/ip/{SERVER_IP}", headers=headers)
        if server_res.status_code != 200:
            print(f"[!] Error al buscar servidor legado ({server_res.status_code}): {server_res.text}")
            sys.exit(1)
            
        server_data = server_res.json().get("server", {})
        servidor_id = server_data.get("id_servidor")
        nombre_servidor = server_data.get("nombre_servidor")
        print(f"[+] Servidor encontrado: {nombre_servidor} (ID: {servidor_id}, Legacy: {server_data.get('es_legacy')})")

        # 3. Obtener instancias DBMS del servidor
        print(f"\n[*] Buscando instancias DBMS en {nombre_servidor}...")
        instancias_res = client.get(f"/sgir/v1/crud/instancias/servidor/{servidor_id}", headers=headers)
        if instancias_res.status_code != 200:
            print(f"[!] Error al obtener instancias ({instancias_res.status_code}): {instancias_res.text}")
            sys.exit(1)
            
        instancias = instancias_res.json()
        if not instancias:
            print("[!] No hay instancias registradas para este servidor.")
            sys.exit(1)
            
        instancia = instancias[0]
        instancia_id = instancia["id_instancia"]
        print(f"[+] Instancia DBMS seleccionada: {instancia['nombre_instancia']} (ID: {instancia_id})")

        # 4. Obtener credenciales SSH
        print(f"\n[*] Obteniendo credenciales de acceso para el servidor...")
        credenciales_res = client.get(f"/sgir/v1/crud/credenciales/servidor/{servidor_id}", headers=headers)
        if credenciales_res.status_code != 200:
            print(f"[!] Error al obtener credenciales ({credenciales_res.status_code}): {credenciales_res.text}")
            sys.exit(1)
            
        credenciales = credenciales_res.json()
        # Filtrar por acceso SSH (id_tipo_acceso == 1)
        credencial_id = None
        for c in credenciales:
            tipo_id = c["id_tipo_acceso"] if "id_tipo_acceso" in c else c.get("tipo", {}).get("id_tipo_acceso")
            if tipo_id == 1:
                credencial_id = c["id_credencial"]
                print(f"[+] Credencial SSH elegida: Usuario '{c['usuario']}' (ID: {credencial_id})")
                break
                
        if not credencial_id:
            print("[!] No se encontró ninguna credencial SSH configurada.")
            sys.exit(1)

        # 5. Obtener rutas de respaldo del servidor
        print(f"\n[*] Obteniendo rutas de respaldo...")
        rutas_res = client.get(f"/sgir/v1/crud/rutas-respaldo/servidor/{servidor_id}", headers=headers)
        if rutas_res.status_code != 200:
            print(f"[!] Error al obtener rutas de respaldo ({rutas_res.status_code}): {rutas_res.text}")
            sys.exit(1)
            
        rutas = rutas_res.json()
        if not rutas:
            print("[!] No se encontraron rutas de respaldo configuradas para el servidor.")
            sys.exit(1)
            
        # 6. Iterar sobre las rutas de respaldo disponibles hasta encontrar archivos físicos
        target_file_path = None
        
        print(f"\n[*] Se encontraron {len(rutas)} rutas de respaldo. Escaneando secuencialmente...")
        for r in rutas:
            ruta_id = r["id_ruta"]
            ruta_path = r["path"]
            print(f"\n[*] Iniciando descubrimiento de respaldos en la ruta: {ruta_path} (ID: {ruta_id})...")
            
            endpoint_discover = f"/sgir/v1/m3/inventory/discover-backups/{instancia_id}/{credencial_id}/{ruta_id}"
            discover_res = client.post(endpoint_discover, headers=headers)
            
            if discover_res.status_code != 200:
                print(f"[!] Error al escanear ruta {ruta_path}: {discover_res.text}")
                continue
                
            discover_data = discover_res.json()
            archivos_procesados = discover_data.get('archivos_procesados', 0)
            print(f"[+] Escaneo de ruta completo. Archivos procesados: {archivos_procesados}")
            
            # Buscar el primer archivo físico encontrado
            details = discover_data.get("detalles", [])
            for d in details:
                if d.get("ruta_path"):
                    target_file_path = d["ruta_path"]
                    break
                    
            if target_file_path:
                print(f"[+] Archivo remoto localizado para transferencia directa: {target_file_path}")
                break
            else:
                print(f"[-] No se localizaron archivos físicos en la ruta {ruta_path}, intentando con la siguiente ruta...")
                
        if not target_file_path:
            print(f"\n[!] Error: Se escanearon todas las rutas de respaldo ({len(rutas)}) para el servidor {SERVER_IP}, pero no se localizó ningún archivo físico en el servidor remoto.")
            sys.exit(1)
            
        # 7. Ejecutar la transferencia directa por ruta física (respaldo_id = 0)
        print(f"\n[*] Ejecutando transferencia directa por ruta física (respaldo_id = 0) para: {target_file_path}...")
        replicate_payload = {
            "destino_ruta_id": None,
            "remote_path": target_file_path,
            "servidor_id": servidor_id,
            "credencial_id": credencial_id
        }
        replicate_res = client.post(f"/sgir/v1/crud/respaldos/0/replicate", json=replicate_payload, headers=headers)
        
        print(f"\n[=] Respuesta del Servidor ({replicate_res.status_code}):")
        if replicate_res.status_code == 200:
            print("[+] ¡Workflow de transferencia directa (sin registro previo en DB) completado exitosamente!")
            print(json.dumps(replicate_res.json(), indent=2, ensure_ascii=False))
        else:
            print(f"[!] Fallo en el endpoint de replicación directa: {replicate_res.text}")
            sys.exit(1)





if __name__ == "__main__":
    try:
        run_test()
    except Exception as e:
        print(f"[!] Error inesperado: {str(e)}")
        sys.exit(1)
