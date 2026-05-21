import unittest
import httpx
import time
import json

class TestModularDBMonitoring(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.base_url = "http://localhost:8000"
        cls.client = httpx.Client(base_url=cls.base_url)
        cls.token = None
        cls.headers = {}
        
        # Almacén de IDs por motor
        cls.ids = {
            "id_estado": 1,
            "id_acceso_db": 2,
            "dbms": {
                "mysql5": 2,
                "mysql8": 3,
                "mongodb": 5
            },
            "mysql5": {
                "id_servidor": None,
                "id_credencial": None,
                "id_instancia": None
            },
            "mysql8": {
                "id_servidor": None,
                "id_credencial": None,
                "id_instancia": None
            },
            "mongodb": {
                "id_servidor": None,
                "id_credencial": None,
                "id_instancia": None
            }
        }
        cls.criticidad_ids = {}

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

    def test_02_resolve_catalogs_and_criticalities(self):
        """2. Catálogos: Resuelve o crea los niveles de criticidad (Bajo, Medio, Alto) y estado."""
        self.assertIsNotNone(self.token)

        # A. Resolver Estado Activo
        res = self.client.get("/sgir/v1/crud/estados/", headers=self.headers)
        if res.status_code == 200 and res.json():
            self.__class__.ids["id_estado"] = res.json()[0]["id_estado"]
        else:
            c_res = self.client.post("/sgir/v1/crud/estados/", json={"nombre_estado": "Activo"}, headers=self.headers)
            if c_res.status_code == 201:
                self.__class__.ids["id_estado"] = c_res.json()["id_estado"]

        # B. Resolver Tipo Acceso DB Native
        res = self.client.get("/sgir/v1/crud/tipo-acceso/", headers=self.headers)
        if res.status_code == 200 and res.json():
            for acc in res.json():
                if "native" in acc["nombre_tipo"].lower() or "db" in acc["nombre_tipo"].lower():
                    self.__class__.ids["id_acceso_db"] = acc["id_tipo_acceso"]
                    break

        # C. Resolver DBMS IDs
        res = self.client.get("/sgir/v1/crud/dbms/", headers=self.headers)
        if res.status_code == 200 and res.json():
            for dbms in res.json():
                name = dbms["nombre_dbms"].lower()
                if "mysql 5" in name or "mysql5" in name:
                    self.__class__.ids["dbms"]["mysql5"] = dbms["id_dbms"]
                elif "mysql 8" in name or "mysql8" in name:
                    self.__class__.ids["dbms"]["mysql8"] = dbms["id_dbms"]
                elif "mongo" in name:
                    self.__class__.ids["dbms"]["mongodb"] = dbms["id_dbms"]

        # D. Resolver Niveles de Criticidad (Bajo, Medio, Alto)
        res = self.client.get("/sgir/v1/crud/criticidad/", headers=self.headers)
        levels = {}
        if res.status_code == 200:
            for nc in res.json():
                name = nc["nombre_nivel"].lower()
                if "bajo" in name:
                    levels["Bajo"] = nc["id_nivel_criticidad"]
                elif "medio" in name:
                    levels["Medio"] = nc["id_nivel_criticidad"]
                elif "alto" in name:
                    levels["Alto"] = nc["id_nivel_criticidad"]
        
        # Si falta alguno, lo creamos para el test
        if "Bajo" not in levels:
            c_res = self.client.post("/sgir/v1/crud/criticidad/", json={"nombre_nivel": "Bajo", "descripcion": "Monitoreo Bajo"}, headers=self.headers)
            if c_res.status_code == 201:
                levels["Bajo"] = c_res.json()["id_nivel_criticidad"]
        if "Medio" not in levels:
            c_res = self.client.post("/sgir/v1/crud/criticidad/", json={"nombre_nivel": "Medio", "descripcion": "Monitoreo Medio"}, headers=self.headers)
            if c_res.status_code == 201:
                levels["Medio"] = c_res.json()["id_nivel_criticidad"]
        if "Alto" not in levels:
            c_res = self.client.post("/sgir/v1/crud/criticidad/", json={"nombre_nivel": "Alto", "descripcion": "Monitoreo Alto"}, headers=self.headers)
            if c_res.status_code == 201:
                levels["Alto"] = c_res.json()["id_nivel_criticidad"]

        self.__class__.criticidad_ids = levels
        print(f"[TEST] Catálogos resueltos e Niveles de Criticidad: {levels}")

    def _setup_target(self, engine_key: str, srv_name: str, inst_name: str, port: int, user: str, db_pass: str):
        """Helper para registrar/encontrar servidor, credencial e instancia de forma robusta."""
        self.assertIsNotNone(self.token)

        # 1. Resolver/Crear Servidor
        srv_payload = {
            "nombre_servidor": srv_name,
            "direccion_ip": srv_name,  # Usamos nombre del contenedor en red de Docker
            "es_legacy": False,
            "descripcion": f"Contenedor de pruebas {engine_key.upper()}",
            "monitoreo_host": False,
            "monitoreo_db": True,
            "id_nivel_criticidad": self.criticidad_ids.get("Bajo", 1),
            "id_estado_servidor": self.ids["id_estado"]
        }
        res = self.client.post("/sgir/v1/crud/servidores/", json=srv_payload, headers=self.headers)
        if res.status_code == 201:
            self.__class__.ids[engine_key]["id_servidor"] = res.json()["id_servidor"]
        else:
            list_res = self.client.get("/sgir/v1/crud/servidores/", headers=self.headers)
            for srv in list_res.json():
                if srv["nombre_servidor"] == srv_name:
                    self.__class__.ids[engine_key]["id_servidor"] = srv["id_servidor"]
                    if srv["direccion_ip"] in ["127.0.0.1", "localhost"]:
                        self.client.put(
                            f"/sgir/v1/crud/servidores/{srv['id_servidor']}",
                            json={"direccion_ip": srv_name},
                            headers=self.headers
                        )
                    break
        self.assertIsNotNone(self.ids[engine_key]["id_servidor"], f"Servidor {srv_name} no resuelto.")

        # 2. Resolver/Crear Credencial
        cred_payload = {
            "usuario": user,
            "password": db_pass,
            "id_tipo_acceso": self.ids["id_acceso_db"],
            "id_estado_credencial": self.ids["id_estado"],
            "id_servidor": self.ids[engine_key]["id_servidor"]
        }
        res = self.client.post("/sgir/v1/crud/credenciales/", json=cred_payload, headers=self.headers)
        if res.status_code == 201:
            self.__class__.ids[engine_key]["id_credencial"] = res.json()["id_credencial"]
        else:
            list_res = self.client.get(f"/sgir/v1/crud/credenciales/servidor/{self.ids[engine_key]['id_servidor']}", headers=self.headers)
            for cred in list_res.json():
                if cred["usuario"] == user:
                    self.__class__.ids[engine_key]["id_credencial"] = cred["id_credencial"]
                    break
        self.assertIsNotNone(self.ids[engine_key]["id_credencial"], f"Credencial para {srv_name} no resuelta.")

        # 3. Resolver/Crear Instancia
        inst_payload = {
            "nombre_instancia": inst_name,
            "puerto": port,
            "id_servidor": self.ids[engine_key]["id_servidor"],
            "id_dbms": self.ids["dbms"][engine_key],
            "id_estado_instancia": self.ids["id_estado"]
        }
        res = self.client.post("/sgir/v1/crud/instancias/", json=inst_payload, headers=self.headers)
        if res.status_code == 201:
            self.__class__.ids[engine_key]["id_instancia"] = res.json()["id_instancia"]
        else:
            list_res = self.client.get(f"/sgir/v1/crud/instancias/servidor/{self.ids[engine_key]['id_servidor']}", headers=self.headers)
            for inst in list_res.json():
                if inst["nombre_instancia"] == inst_name:
                    self.__class__.ids[engine_key]["id_instancia"] = inst["id_instancia"]
                    break
        self.assertIsNotNone(self.ids[engine_key]["id_instancia"], f"Instancia {inst_name} no resuelta.")
        
        print(f"[TEST] Target {engine_key.upper()} configurado -> Servidor ID: {self.ids[engine_key]['id_servidor']}, Credencial ID: {self.ids[engine_key]['id_credencial']}, Instancia ID: {self.ids[engine_key]['id_instancia']}")

    def test_03_setup_mysql5_target(self):
        """3. Configura el target de MySQL 5 (sgir_mysql5)."""
        self._setup_target("mysql5", "sgir_mysql5", "sgir_db_5", 3305, "sgir_monitoreo", "123Nokia$")

    def test_04_setup_mysql8_target(self):
        """4. Configura el target de MySQL 8 (sgir_mysql8)."""
        self._setup_target("mysql8", "sgir_mysql8", "sgir_db_8", 3308, "sgir_monitoreo", "123Nokia$")

    def test_05_setup_mongodb_target(self):
        """5. Configura el target de MongoDB (sgir_mongodb)."""
        self._setup_target("mongodb", "sgir_mongodb", "admin", 27017, "sgir_monitoreo", "123Nokia$")

    def _test_engine_modular_monitoring(self, engine_key: str):
        """Helper para iterar por niveles de criticidad (Bajo, Medio, Alto) y verificar la modularidad."""
        srv_id = self.ids[engine_key]["id_servidor"]
        inst_id = self.ids[engine_key]["id_instancia"]
        cred_id = self.ids[engine_key]["id_credencial"]
        
        self.assertIsNotNone(srv_id)
        self.assertIsNotNone(inst_id)
        self.assertIsNotNone(cred_id)
        
        endpoint = f"/sgir/v1/m1/{engine_key}/modular/{inst_id}/{cred_id}"

        # -------------------------------------------------------------
        # Nivel A: CRITICIDAD BAJA (Solo Grupo A)
        # -------------------------------------------------------------
        bajo_id = self.criticidad_ids["Bajo"]
        upd_res = self.client.put(
            f"/sgir/v1/crud/servidores/{srv_id}",
            json={"id_nivel_criticidad": bajo_id},
            headers=self.headers
        )
        self.assertEqual(upd_res.status_code, 200, f"Error al actualizar criticidad a Bajo para {engine_key}")
        
        res = self.client.get(endpoint, headers=self.headers)
        self.assertEqual(res.status_code, 200, f"Error al llamar endpoint modular para {engine_key} en nivel Bajo: {res.text}")
        data = res.json()
        print(f"\n📈 [{engine_key.upper()} - BAJO] Respuesta recibida:")
        print(json.dumps(data, indent=2, ensure_ascii=False))
        
        self.assertEqual(data["nivel_criticidad"].lower(), "bajo")
        self.assertIsNotNone(data.get("grupo_a"), "El Grupo A (Conectividad) debe estar presente.")
        self.assertIsNone(data.get("grupo_b"), "El Grupo B debe ser nulo para criticidad Bajo.")
        self.assertIsNone(data.get("grupo_c"), "El Grupo C debe ser nulo para criticidad Bajo.")

        # -------------------------------------------------------------
        # Nivel B: CRITICIDAD MEDIA (Grupos A + B)
        # -------------------------------------------------------------
        medio_id = self.criticidad_ids["Medio"]
        upd_res = self.client.put(
            f"/sgir/v1/crud/servidores/{srv_id}",
            json={"id_nivel_criticidad": medio_id},
            headers=self.headers
        )
        self.assertEqual(upd_res.status_code, 200, f"Error al actualizar criticidad a Medio para {engine_key}")
        
        res = self.client.get(endpoint, headers=self.headers)
        self.assertEqual(res.status_code, 200, f"Error al llamar endpoint modular para {engine_key} en nivel Medio: {res.text}")
        data = res.json()
        print(f"\n📈 [{engine_key.upper()} - MEDIO] Respuesta recibida:")
        print(json.dumps(data, indent=2, ensure_ascii=False))
        
        self.assertEqual(data["nivel_criticidad"].lower(), "medio")
        self.assertIsNotNone(data.get("grupo_a"), "El Grupo A (Conectividad) debe estar presente.")
        self.assertIsNotNone(data.get("grupo_b"), "El Grupo B (Recursos) debe estar presente para criticidad Medio.")
        self.assertIsNone(data.get("grupo_c"), "El Grupo C debe ser nulo para criticidad Medio.")

        # -------------------------------------------------------------
        # Nivel C: CRITICIDAD ALTA (Grupos A + B + C)
        # -------------------------------------------------------------
        alto_id = self.criticidad_ids["Alto"]
        upd_res = self.client.put(
            f"/sgir/v1/crud/servidores/{srv_id}",
            json={"id_nivel_criticidad": alto_id},
            headers=self.headers
        )
        self.assertEqual(upd_res.status_code, 200, f"Error al actualizar criticidad a Alto para {engine_key}")
        
        res = self.client.get(endpoint, headers=self.headers)
        self.assertEqual(res.status_code, 200, f"Error al llamar endpoint modular para {engine_key} en nivel Alto: {res.text}")
        data = res.json()
        print(f"\n📈 [{engine_key.upper()} - ALTO] Respuesta recibida:")
        print(json.dumps(data, indent=2, ensure_ascii=False))
        
        self.assertEqual(data["nivel_criticidad"].lower(), "alto")
        self.assertIsNotNone(data.get("grupo_a"), "El Grupo A (Conectividad) debe estar presente.")
        self.assertIsNotNone(data.get("grupo_b"), "El Grupo B (Recursos) debe estar presente para criticidad Alto.")
        self.assertIsNotNone(data.get("grupo_c"), "El Grupo C (Performance) debe estar presente para criticidad Alto.")

    def test_06_mysql5_modular_monitoring(self):
        """6. Pruebas de criticidad modular en MySQL 5."""
        print("\n--- INICIANDO PRUEBAS MODULARES MYSQL 5 ---")
        self._test_engine_modular_monitoring("mysql5")

    def test_07_mysql8_modular_monitoring(self):
        """7. Pruebas de criticidad modular en MySQL 8."""
        print("\n--- INICIANDO PRUEBAS MODULARES MYSQL 8 ---")
        self._test_engine_modular_monitoring("mysql8")

    def test_08_mongodb_modular_monitoring(self):
        """8. Pruebas de criticidad modular en MongoDB."""
        print("\n--- INICIANDO PRUEBAS MODULARES MONGODB ---")
        self._test_engine_modular_monitoring("mongodb")

if __name__ == "__main__":
    unittest.main()
