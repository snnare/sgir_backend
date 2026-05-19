import unittest
import httpx
import time
import json

class TestMongoDBMonitoring(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.base_url = "http://localhost:8000"
        cls.client = httpx.Client(base_url=cls.base_url)
        cls.token = None
        cls.headers = {}
        
        # Almacén de IDs necesarios para la prueba
        cls.ids = {
            "id_servidor": None,
            "id_credencial": None,
            "id_instancia": None,
            "id_estado": 1,
            "id_acceso_db": 2,
            "id_dbms_mongo": 5
        }

    @classmethod
    def tearDownClass(cls):
        cls.client.close()

    def test_01_login(self):
        """1. Inicia sesión como administrador para obtener el token JWT."""
        login_payload = {
            "username": "admin@admin.com",
            "password": "123Nokia"
        }
        response = self.client.post("/sgir/v1/crud/users/login", data=login_payload)
        self.assertEqual(response.status_code, 200, "Error de login. ¿Se ejecutó 00_base.py?")
        token_data = response.json()
        self.assertIn("access_token", token_data)
        
        self.__class__.token = token_data["access_token"]
        self.__class__.headers = {"Authorization": f"Bearer {self.token}"}
        print("\n[TEST] Autenticado exitosamente. Token listo.")

    def test_02_resolve_catalogs(self):
        """2. Catálogos: Resuelve los IDs de Estado, Acceso DB y DBMS MongoDB."""
        self.assertIsNotNone(self.token)

        # A. Resolver Estado Activo
        res = self.client.get("/sgir/v1/crud/estados/", headers=self.headers)
        if res.status_code == 200 and res.json():
            self.__class__.ids["id_estado"] = res.json()[0]["id_estado"]

        # B. Resolver Tipo Acceso DB Native
        res = self.client.get("/sgir/v1/crud/tipo-acceso/", headers=self.headers)
        if res.status_code == 200 and res.json():
            for acc in res.json():
                if "native" in acc["nombre_tipo"].lower() or "db" in acc["nombre_tipo"].lower():
                    self.__class__.ids["id_acceso_db"] = acc["id_tipo_acceso"]
                    break

        # C. Resolver DBMS MongoDB ID
        res = self.client.get("/sgir/v1/crud/dbms/", headers=self.headers)
        if res.status_code == 200 and res.json():
            for dbms in res.json():
                if "mongo" in dbms["nombre_dbms"].lower():
                    self.__class__.ids["id_dbms_mongo"] = dbms["id_dbms"]
                    break
        
        print(f"[TEST] Catálogos resueltos -> Estado: {self.ids['id_estado']}, Acceso DB: {self.ids['id_acceso_db']}, DBMS Mongo: {self.ids['id_dbms_mongo']}")

    def test_03_setup_mongodb_target(self):
        """3. Infraestructura: Registra o actualiza el servidor MongoDB, sus credenciales e instancia."""
        self.assertIsNotNone(self.token)

        # A. Obtener o crear servidor "sgir_mongodb"
        srv_payload = {
            "nombre_servidor": "sgir_mongodb",
            "direccion_ip": "sgir_mongodb",  # Usar el nombre del contenedor para la red de Docker
            "es_legacy": False,
            "descripcion": "Contenedor de MongoDB para pruebas",
            "monitoreo_host": False,
            "monitoreo_db": True,
            "id_nivel_criticidad": 1,
            "id_estado_servidor": self.ids["id_estado"]
        }
        res = self.client.post("/sgir/v1/crud/servidores/", json=srv_payload, headers=self.headers)
        if res.status_code == 201:
            self.__class__.ids["id_servidor"] = res.json()["id_servidor"]
        else:
            # Buscar preexistente
            list_res = self.client.get("/sgir/v1/crud/servidores/", headers=self.headers)
            for srv in list_res.json():
                if srv["nombre_servidor"] == "sgir_mongodb":
                    self.__class__.ids["id_servidor"] = srv["id_servidor"]
                    # Auto-curación si la IP preexistente es local (127.0.0.1)
                    if srv["direccion_ip"] in ["127.0.0.1", "localhost"]:
                        self.client.put(
                            f"/sgir/v1/crud/servidores/{srv['id_servidor']}",
                            json={"direccion_ip": "sgir_mongodb"},
                            headers=self.headers
                        )
                    break

        self.assertIsNotNone(self.ids["id_servidor"], "Debe existir el servidor MongoDB.")

        # B. Obtener o crear Credencial (sgir / sgir)
        cred_payload = {
            "usuario": "sgir",
            "password": "sgir",
            "id_tipo_acceso": self.ids["id_acceso_db"],
            "id_estado_credencial": self.ids["id_estado"],
            "id_servidor": self.ids["id_servidor"]
        }
        res = self.client.post("/sgir/v1/crud/credenciales/", json=cred_payload, headers=self.headers)
        if res.status_code == 201:
            self.__class__.ids["id_credencial"] = res.json()["id_credencial"]
        else:
            # Buscar preexistente
            list_res = self.client.get(f"/sgir/v1/crud/credenciales/servidor/{self.ids['id_servidor']}", headers=self.headers)
            for cred in list_res.json():
                if cred["usuario"] == "sgir":
                    self.__class__.ids["id_credencial"] = cred["id_credencial"]
                    break

        self.assertIsNotNone(self.ids["id_credencial"], "Debe existir la credencial de MongoDB.")

        # C. Obtener o crear Instancia (admin / puerto 27017)
        inst_payload = {
            "nombre_instancia": "admin",
            "puerto": 27017,
            "id_servidor": self.ids["id_servidor"],
            "id_dbms": self.ids["id_dbms_mongo"],
            "id_estado_instancia": self.ids["id_estado"]
        }
        res = self.client.post("/sgir/v1/crud/instancias/", json=inst_payload, headers=self.headers)
        if res.status_code == 201:
            self.__class__.ids["id_instancia"] = res.json()["id_instancia"]
        else:
            # Buscar preexistente
            list_res = self.client.get(f"/sgir/v1/crud/instancias/servidor/{self.ids['id_servidor']}", headers=self.headers)
            for inst in list_res.json():
                if inst["nombre_instancia"] == "admin":
                    self.__class__.ids["id_instancia"] = inst["id_instancia"]
                    break

        self.assertIsNotNone(self.ids["id_instancia"], "Debe existir la instancia de MongoDB.")
        print(f"[TEST] Target MongoDB configurado -> Servidor ID: {self.ids['id_servidor']}, Credencial ID: {self.ids['id_credencial']}, Instancia ID: {self.ids['id_instancia']}")

    def test_04_realtime_mongodb_monitoring(self):
        """4. Monitoreo: Realiza consultas al endpoint de monitoreo en tiempo real por 5 segundos."""
        self.assertIsNotNone(self.ids["id_servidor"])
        self.assertIsNotNone(self.ids["id_credencial"])

        print("\n--- [PROBANDO MONITOREO MONGODB (REAL-TIME POR 5 SEGUNDOS)] ---")

        for i in range(1, 6):
            start_time = time.time()
            mon_res = self.client.get(
                f"/sgir/v1/m1/mongodb/{self.ids['id_servidor']}/{self.ids['id_credencial']}",
                headers=self.headers
            )
            
            if mon_res.status_code == 200:
                data = mon_res.json()
                print(f"\n⏱️ [Segundo {i}] Respuesta recibida (MongoDB):")
                print(json.dumps(data, indent=2, ensure_ascii=False))
                
                # Comprobaciones básicas de los datos de MongoDB
                self.assertEqual(data.get("status"), "online", "El estado de MongoDB debe ser 'online'")
                self.assertGreater(data.get("uptime", 0), 0, "El uptime de MongoDB debe ser mayor a 0")
                self.assertEqual(data.get("ok"), 1.0, "La respuesta del servidorStatus de Mongo debe tener ok: 1.0")
                self.assertIn("connections_current", data, "Debe reportar conexiones actuales")
                self.assertIn("mem_resident_mb", data, "Debe reportar uso de memoria residente")
            else:
                self.fail(f"[ERROR] Código de estado {mon_res.status_code}: {mon_res.text}")
                
            elapsed = time.time() - start_time
            sleep_time = max(0.1, 1.0 - elapsed)
            if i < 5:
                time.sleep(sleep_time)

if __name__ == "__main__":
    unittest.main()
