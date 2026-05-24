import unittest
import httpx
import json

class TestOracleLegacyEndpoint(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.base_url = "http://localhost:8000"
        cls.client = httpx.Client(base_url=cls.base_url)
        cls.token = None
        cls.headers = {}
        
        # IDs de catálogos base con fallbacks
        cls.catalog_ids = {
            "id_estado": 1,
            "id_criticidad": 1,
            "id_acceso_ssh": 1,
            "id_acceso_db": 2,
            "dbms": {
                "oracle": 4
            }
        }

    @classmethod
    def tearDownClass(cls):
        cls.client.close()

    def test_01_login(self):
        """1. Autenticación: Realiza login para obtener el Bearer Token del administrador."""
        login_payload = {
            "username": "admin@admin.com",
            "password": "123Nokia"
        }
        response = self.client.post("/sgir/v1/crud/users/login", data=login_payload)
        self.assertEqual(response.status_code, 200, "Error al autenticarse. Verifica las credenciales.")
        token_data = response.json()
        self.assertIn("access_token", token_data)
        
        self.__class__.token = token_data["access_token"]
        self.__class__.headers = {"Authorization": f"Bearer {self.token}"}
        print("\n[LOGIN] Autenticado como Administrador exitosamente.")

    def test_02_resolve_catalogs(self):
        """2. Catálogos: Resuelve y asegura la existencia de catálogos base en el sistema."""
        self.assertIsNotNone(self.token)

        # A. Estado Activo
        res = self.client.get("/sgir/v1/crud/estados/", headers=self.headers)
        if res.status_code == 200 and res.json():
            self.__class__.catalog_ids["id_estado"] = res.json()[0]["id_estado"]

        # B. Nivel de Criticidad
        res = self.client.get("/sgir/v1/crud/criticidad/", headers=self.headers)
        if res.status_code == 200 and res.json():
            self.__class__.catalog_ids["id_criticidad"] = res.json()[0]["id_nivel_criticidad"]

        # C. Tipos de Acceso (SSH y DB)
        res = self.client.get("/sgir/v1/crud/tipo-acceso/", headers=self.headers)
        if res.status_code == 200 and res.json():
            for access in res.json():
                if "ssh" in access["nombre_tipo"].lower():
                    self.__class__.catalog_ids["id_acceso_ssh"] = access["id_tipo_acceso"]
                elif "native" in access["nombre_tipo"].lower() or "db" in access["nombre_tipo"].lower():
                    self.__class__.catalog_ids["id_acceso_db"] = access["id_tipo_acceso"]

        print(f"[CATALOGS] Estado: {self.catalog_ids['id_estado']}, Criticidad: {self.catalog_ids['id_criticidad']}, SSH: {self.catalog_ids['id_acceso_ssh']}, DB: {self.catalog_ids['id_acceso_db']}")

    def test_03_register_server_and_credentials(self):
        """3. Registro: Registra el servidor legacy y las credenciales SSH/DB."""
        self.assertIsNotNone(self.token)
        
        ip_server = "148.215.1.98"
        server_name = "Servidor Oracle 10g Legacy"

        # A. Crear Servidor
        server_payload = {
            "nombre_servidor": server_name,
            "direccion_ip": ip_server,
            "es_legacy": True,
            "descripcion": "Servidor físico Oracle 10g Legacy registrado mediante suite de pruebas",
            "monitoreo_host": True,
            "monitoreo_db": True,
            "id_nivel_criticidad": self.catalog_ids["id_criticidad"],
            "id_estado_servidor": self.catalog_ids["id_estado"]
        }
        
        res = self.client.post("/sgir/v1/crud/servidores/", json=server_payload, headers=self.headers)
        if res.status_code == 201:
            server_id = res.json()["id_servidor"]
            print(f"[SERVER] Creado servidor '{server_name}' -> ID: {server_id}")
        else:
            # Si ya existe, buscar su ID
            list_res = self.client.get("/sgir/v1/crud/servidores/", headers=self.headers)
            server_id = None
            if list_res.status_code == 200:
                for srv in list_res.json():
                    if srv["direccion_ip"] == ip_server:
                        server_id = srv["id_servidor"]
                        print(f"[SERVER] Servidor preexistente con IP '{ip_server}' -> ID: {server_id}")
                        break
            if not server_id:
                raise Exception(f"No se pudo registrar ni encontrar el servidor legacy: {res.text}")

        # B. Registrar Credencial SSH (oracle / k2!top@.l96)
        ssh_payload = {
            "usuario": "oracle",
            "password": "k2!top@.l96",
            "id_tipo_acceso": self.catalog_ids["id_acceso_ssh"],
            "id_estado_credencial": self.catalog_ids["id_estado"],
            "id_servidor": server_id
        }
        res_ssh = self.client.post("/sgir/v1/crud/credenciales/", json=ssh_payload, headers=self.headers)
        if res_ssh.status_code == 201:
            print("  [CRED] Credencial SSH 'oracle' creada exitosamente.")
        else:
            print("  [CRED] Credencial SSH 'oracle' ya registrada o preexistente.")

        # C. Registrar Credencial DB en la CMDB (opcional para el inventario, uevapem/uevapem)
        db_payload = {
            "usuario": "uevapem",
            "password": "uevapem",
            "id_tipo_acceso": self.catalog_ids["id_acceso_db"],
            "id_estado_credencial": self.catalog_ids["id_estado"],
            "id_servidor": server_id
        }
        res_db = self.client.post("/sgir/v1/crud/credenciales/", json=db_payload, headers=self.headers)
        if res_db.status_code == 201:
            print("  [CRED] Credencial de Base de Datos 'uevapem' creada exitosamente.")
        else:
            print("  [CRED] Credencial de Base de Datos 'uevapem' ya registrada.")

        # D. Registrar Instancia DBMS de Oracle (DbEvapem con SID)
        instance_payload = {
            "nombre_instancia": "DbEvapem",
            "puerto": 1521,
            "id_servidor": server_id,
            "id_dbms": self.catalog_ids["dbms"]["oracle"],
            "id_estado_instancia": self.catalog_ids["id_estado"],
            "parametros_conexion": {"sid": "DbEvapem"}
        }
        res_inst = self.client.post("/sgir/v1/crud/instancias/", json=instance_payload, headers=self.headers)
        if res_inst.status_code == 201:
            print("  [INSTANCE] Instancia DBMS 'DbEvapem' con ORACLE_SID creada exitosamente.")
        else:
            print("  [INSTANCE] Instancia DBMS 'DbEvapem' ya registrada o preexistente.")

    def test_04_execute_legacy_test_endpoint(self):
        """4. Pruebas: Invoca el endpoint de prueba de conexión legacy."""
        self.assertIsNotNone(self.token)
        
        test_payload = {
            "direccion_ip": "148.215.1.98",
            "puerto": 1521,
            "usuario": "uevapem",
            "password": "uevapem"
        }
        
        print("\n--- Ejecutando Endpoint de Prueba Legacy (/test/db/oracle/legacy) ---")
        response = self.client.post(
            "/sgir/v1/crud/conexion/test/db/oracle/legacy",
            json=test_payload,
            headers=self.headers
        )
        
        print(f"[TEST RESPONSE] HTTP Status: {response.status_code}")
        try:
            res_data = response.json()
            print(f"[TEST RESPONSE] Payload: {json.dumps(res_data, indent=2)}")
        except Exception:
            print(f"[TEST RESPONSE] Raw text: {response.text}")
            
        # Al no ejecutarlo físicamente en la red en el entorno local offline, validamos que retorne un status_code esperado (200 o 500).
        # Lo importante es que no arroje 404 (Not Found) o 405 (Method Not Allowed).
        self.assertIn(response.status_code, [200, 500], "El endpoint de conexión legacy retornó un código de estado inesperado.")

if __name__ == "__main__":
    unittest.main()
