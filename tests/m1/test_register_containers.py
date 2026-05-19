import unittest
import httpx

class TestRegisterContainers(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.base_url = "http://localhost:8000"
        cls.client = httpx.Client(base_url=cls.base_url)
        cls.token = None
        cls.headers = {}
        
        # IDs de catálogos base (con fallbacks estáticos seguros)
        cls.catalog_ids = {
            "id_estado": 1,
            "id_criticidad": 1,
            "id_acceso_ssh": 1,
            "id_acceso_db": 2,
            "dbms": {
                "mysql5": 2,
                "mysql8": 3,
                "oracle": 4,
                "mongodb": 5
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
        self.assertEqual(response.status_code, 200, "Error al autenticarse. Asegúrate de ejecutar 00_base.py primero.")
        token_data = response.json()
        self.assertIn("access_token", token_data)
        
        self.__class__.token = token_data["access_token"]
        self.__class__.headers = {"Authorization": f"Bearer {self.token}"}
        print("\n[LOGIN] Autenticado como Administrador. Token configurado.")

    def test_02_verify_or_create_catalogs(self):
        """2. Catálogos: Verifica la existencia de catálogos de sistema (Estados, Criticidad, Accesos)."""
        self.assertIsNotNone(self.token)

        # A. Asegurar Estado General (Activo)
        res = self.client.get("/sgir/v1/crud/estados/", headers=self.headers)
        if res.status_code == 200 and res.json():
            self.__class__.catalog_ids["id_estado"] = res.json()[0]["id_estado"]
        else:
            # Intentar crear estado de prueba si no hay ninguno
            create_res = self.client.post("/sgir/v1/crud/estados/", json={"nombre_estado": "Activo"}, headers=self.headers)
            if create_res.status_code == 201:
                self.__class__.catalog_ids["id_estado"] = create_res.json()["id_estado"]

        # B. Asegurar Nivel de Criticidad (Alta/Crítica)
        res = self.client.get("/sgir/v1/crud/criticidad/", headers=self.headers)
        if res.status_code == 200 and res.json():
            self.__class__.catalog_ids["id_criticidad"] = res.json()[0]["id_nivel_criticidad"]
        else:
            create_res = self.client.post("/sgir/v1/crud/criticidad/", json={"nombre_nivel": "Crítica", "descripcion": "Servidores de base de datos"}, headers=self.headers)
            if create_res.status_code == 201:
                self.__class__.catalog_ids["id_criticidad"] = create_res.json()["id_nivel_criticidad"]

        # C. Asegurar Tipo de Acceso SSH (id_tipo_acceso = 1) y DB Native (id_tipo_acceso = 2)
        res = self.client.get("/sgir/v1/crud/tipo-acceso/", headers=self.headers)
        if res.status_code == 200 and res.json():
            for access in res.json():
                if "ssh" in access["nombre_tipo"].lower():
                    self.__class__.catalog_ids["id_acceso_ssh"] = access["id_tipo_acceso"]
                elif "native" in access["nombre_tipo"].lower() or "db" in access["nombre_tipo"].lower():
                    self.__class__.catalog_ids["id_acceso_db"] = access["id_tipo_acceso"]

        print(f"[CATALOGS] IDs resueltos -> Estado: {self.catalog_ids['id_estado']}, Criticidad: {self.catalog_ids['id_criticidad']}, Acceso SSH: {self.catalog_ids['id_acceso_ssh']}, Acceso DB: {self.catalog_ids['id_acceso_db']}")

    def _get_or_create_server(self, name: str, ip: str, description: str) -> int:
        """Helper para registrar un servidor de forma segura evitando duplicidad de nombres."""
        # Si la IP es local y estamos en un entorno dockerizado, usamos el nombre del contenedor
        resolved_ip = name if ip in ["127.0.0.1", "localhost"] else ip
        payload = {
            "nombre_servidor": name,
            "direccion_ip": resolved_ip,
            "es_legacy": False,
            "descripcion": description,
            "monitoreo_host": True,
            "monitoreo_db": True,
            "id_nivel_criticidad": self.catalog_ids["id_criticidad"],
            "id_estado_servidor": self.catalog_ids["id_estado"]
        }
        res = self.client.post("/sgir/v1/crud/servidores/", json=payload, headers=self.headers)
        if res.status_code == 201:
            srv_id = res.json()["id_servidor"]
            print(f"[SERVER CREATED] '{name}' -> ID: {srv_id}")
            return srv_id
        else:
            # Recuperar por listado si ya existe
            list_res = self.client.get("/sgir/v1/crud/servidores/", headers=self.headers)
            if list_res.status_code == 200:
                for srv in list_res.json():
                    if srv["nombre_servidor"] == name:
                        print(f"[SERVER FOUND] '{name}' (preexistente) -> ID: {srv['id_servidor']}")
                        # Si la IP preexistente en la BD es local, la actualizamos para que funcione en Docker
                        if srv["direccion_ip"] in ["127.0.0.1", "localhost"]:
                            self.client.put(
                                f"/sgir/v1/crud/servidores/{srv['id_servidor']}",
                                json={"direccion_ip": resolved_ip},
                                headers=self.headers
                            )
                        return srv["id_servidor"]
            raise Exception(f"No se pudo crear ni encontrar el servidor '{name}': {res.text}")

    def _get_or_create_credential(self, user: str, password: str, access_type: int, server_id: int) -> int:
        """Helper para registrar credenciales de forma segura."""
        payload = {
            "usuario": user,
            "password": password,
            "id_tipo_acceso": access_type,
            "id_estado_credencial": self.catalog_ids["id_estado"],
            "id_servidor": server_id
        }
        res = self.client.post("/sgir/v1/crud/credenciales/", json=payload, headers=self.headers)
        if res.status_code == 201:
            cred_id = res.json()["id_credencial"]
            print(f"  [CRED CREATED] Usuario '{user}' -> ID: {cred_id}")
            return cred_id
        else:
            # Buscar en las credenciales del servidor si ya existe
            list_res = self.client.get(f"/sgir/v1/crud/credenciales/servidor/{server_id}", headers=self.headers)
            if list_res.status_code == 200:
                for cred in list_res.json():
                    if cred["usuario"] == user and cred["id_tipo_acceso"] == access_type:
                        print(f"  [CRED FOUND] Usuario '{user}' (preexistente) -> ID: {cred['id_credencial']}")
                        return cred["id_credencial"]
            raise Exception(f"No se pudo registrar la credencial para '{user}' en servidor {server_id}: {res.text}")

    def _get_or_create_instance(self, name: str, port: int, server_id: int, dbms_id: int) -> int:
        """Helper para registrar una instancia de DBMS de forma segura."""
        payload = {
            "nombre_instancia": name,
            "puerto": port,
            "id_servidor": server_id,
            "id_dbms": dbms_id,
            "id_estado_instancia": self.catalog_ids["id_estado"]
        }
        res = self.client.post("/sgir/v1/crud/instancias/", json=payload, headers=self.headers)
        if res.status_code == 201:
            inst_id = res.json()["id_instancia"]
            print(f"  [INSTANCE CREATED] Instancia '{name}' -> ID: {inst_id}")
            return inst_id
        else:
            # Buscar instancias del servidor
            list_res = self.client.get(f"/sgir/v1/crud/instancias/servidor/{server_id}", headers=self.headers)
            if list_res.status_code == 200:
                for inst in list_res.json():
                    if inst["nombre_instancia"] == name:
                        print(f"  [INSTANCE FOUND] Instancia '{name}' (preexistente) -> ID: {inst['id_instancia']}")
                        return inst["id_instancia"]
            raise Exception(f"No se pudo registrar la instancia '{name}' en servidor {server_id}: {res.text}")

    def test_03_register_mysql5(self):
        """3. MySQL 5: Registra el contenedor sgir_mysql5, credenciales de DB e instancia."""
        self.assertIsNotNone(self.token)
        print("\n--- Registrando MySQL 5 (sgir_mysql5) ---")
        
        # Servidor
        srv_id = self._get_or_create_server("sgir_mysql5", "127.0.0.1", "Contenedor de pruebas MySQL 5.7")
        # Credenciales DB Native
        self._get_or_create_credential("sgir", "sgir", self.catalog_ids["id_acceso_db"], srv_id)
        # Instancia DBMS
        self._get_or_create_instance("sgir_db_5", 3305, srv_id, self.catalog_ids["dbms"]["mysql5"])

    def test_04_register_mysql8(self):
        """4. MySQL 8: Registra el contenedor sgir_mysql8, credenciales de DB e instancia."""
        self.assertIsNotNone(self.token)
        print("\n--- Registrando MySQL 8 (sgir_mysql8) ---")
        
        # Servidor
        srv_id = self._get_or_create_server("sgir_mysql8", "127.0.0.1", "Contenedor de pruebas MySQL 8.0")
        # Credenciales DB Native
        self._get_or_create_credential("sgir", "sgir", self.catalog_ids["id_acceso_db"], srv_id)
        # Instancia DBMS
        self._get_or_create_instance("sgir_db_8", 3308, srv_id, self.catalog_ids["dbms"]["mysql8"])

    def test_05_register_oracle(self):
        """5. Oracle 21c: Registra el contenedor sgir_oracle21c, credenciales de DB e instancia."""
        self.assertIsNotNone(self.token)
        print("\n--- Registrando Oracle 21c (sgir_oracle21c) ---")
        
        # Servidor
        srv_id = self._get_or_create_server("sgir_oracle21c", "127.0.0.1", "Contenedor de pruebas Oracle Express 21c")
        # Credenciales DB Native
        self._get_or_create_credential("system", "123Nokia$", self.catalog_ids["id_acceso_db"], srv_id)
        # Instancia DBMS
        self._get_or_create_instance("XEPDB1", 1521, srv_id, self.catalog_ids["dbms"]["oracle"])

    def test_06_register_mongodb(self):
        """6. MongoDB: Registra el contenedor sgir_mongodb, credenciales de DB e instancia."""
        self.assertIsNotNone(self.token)
        print("\n--- Registrando MongoDB (sgir_mongodb) ---")
        
        # Servidor
        srv_id = self._get_or_create_server("sgir_mongodb", "127.0.0.1", "Contenedor de pruebas MongoDB")
        # Credenciales DB Native
        self._get_or_create_credential("sgir", "sgir", self.catalog_ids["id_acceso_db"], srv_id)
        # Instancia DBMS
        self._get_or_create_instance("admin", 27017, srv_id, self.catalog_ids["dbms"]["mongodb"])

    def test_07_register_ssh_server(self):
        """7. SSH Server: Registra el contenedor sgir_ssh_server y sus credenciales SSH."""
        self.assertIsNotNone(self.token)
        print("\n--- Registrando SSH Server (sgir_ssh_server) ---")
        
        # Servidor
        srv_id = self._get_or_create_server("sgir_ssh_server", "127.0.0.1", "Contenedor Openssh-server genérico para pruebas")
        # Credenciales SSH (puerto 2222 mapeado en Docker Compose)
        self._get_or_create_credential("sgir_user", "sgir_pass", self.catalog_ids["id_acceso_ssh"], srv_id)

    def test_08_register_ubuntu(self):
        """8. Ubuntu SSH: Registra el contenedor sgir_ubuntu_stable y sus credenciales SSH."""
        self.assertIsNotNone(self.token)
        print("\n--- Registrando Ubuntu Stable SSH (sgir_ubuntu_stable) ---")
        
        # Servidor
        srv_id = self._get_or_create_server("sgir_ubuntu_stable", "127.0.0.1", "Contenedor Ubuntu 22.04 SSH para pruebas")
        # Credenciales SSH (puerto 2223 mapeado en Docker Compose)
        self._get_or_create_credential("sgir_user", "sgir_pass", self.catalog_ids["id_acceso_ssh"], srv_id)

    def test_09_register_fedora(self):
        """9. Fedora SSH: Registra el contenedor sgir_fedora_latest y sus credenciales SSH."""
        self.assertIsNotNone(self.token)
        print("\n--- Registrando Fedora Latest SSH (sgir_fedora_latest) ---")
        
        # Servidor
        srv_id = self._get_or_create_server("sgir_fedora_latest", "127.0.0.1", "Contenedor Fedora Latest SSH para pruebas")
        # Credenciales SSH (puerto 22 mapeado en Docker Compose)
        self._get_or_create_credential("sgir_user", "sgir_pass", self.catalog_ids["id_acceso_ssh"], srv_id)

if __name__ == "__main__":
    unittest.main()
