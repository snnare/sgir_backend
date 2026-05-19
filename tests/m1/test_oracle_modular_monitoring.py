import unittest
import httpx
import time
import json

class TestOracleModularMonitoring(unittest.TestCase):
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
            "id_dbms_oracle": 4
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

        # C. Resolver DBMS Oracle ID
        res = self.client.get("/sgir/v1/crud/dbms/", headers=self.headers)
        if res.status_code == 200 and res.json():
            for dbms in res.json():
                if "oracle" in dbms["nombre_dbms"].lower():
                    self.__class__.ids["id_dbms_oracle"] = dbms["id_dbms"]
                    break

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
        print(f"[TEST] Criticidades mapeadas -> Bajo: {levels.get('Bajo')}, Medio: {levels.get('Medio')}, Alto: {levels.get('Alto')}")

    def test_03_setup_oracle_target(self):
        """3. Infraestructura: Verifica o registra el servidor Oracle, credenciales e instancia."""
        self.assertIsNotNone(self.token)

        # A. Obtener o crear servidor "sgir_oracle21c"
        srv_payload = {
            "nombre_servidor": "sgir_oracle21c",
            "direccion_ip": "sgir_oracle21c",  # Usar el nombre del contenedor en la red de docker
            "es_legacy": False,
            "descripcion": "Contenedor de Oracle para Monitoreo Modular",
            "monitoreo_host": False,
            "monitoreo_db": True,
            "id_nivel_criticidad": self.criticidad_ids.get("Bajo", 1),
            "id_estado_servidor": self.ids["id_estado"]
        }
        res = self.client.post("/sgir/v1/crud/servidores/", json=srv_payload, headers=self.headers)
        if res.status_code == 201:
            self.__class__.ids["id_servidor"] = res.json()["id_servidor"]
        else:
            # Buscar preexistente
            list_res = self.client.get("/sgir/v1/crud/servidores/", headers=self.headers)
            for srv in list_res.json():
                if srv["nombre_servidor"] == "sgir_oracle21c":
                    self.__class__.ids["id_servidor"] = srv["id_servidor"]
                    # Si la IP preexistente es local, la actualizamos para que funcione en la red de Docker
                    if srv["direccion_ip"] in ["127.0.0.1", "localhost"]:
                        self.client.put(
                            f"/sgir/v1/crud/servidores/{srv['id_servidor']}",
                            json={"direccion_ip": "sgir_oracle21c"},
                            headers=self.headers
                        )
                    break

        self.assertIsNotNone(self.ids["id_servidor"], "Debe existir el servidor Oracle de pruebas.")

        # B. Obtener o crear Credencial (system / 123Nokia$)
        cred_payload = {
            "usuario": "system",
            "password": "123Nokia$",
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
                if cred["usuario"] == "system":
                    self.__class__.ids["id_credencial"] = cred["id_credencial"]
                    break

        self.assertIsNotNone(self.ids["id_credencial"], "Debe existir la credencial de Oracle.")

        # C. Obtener o crear Instancia (XEPDB1 / puerto 1521)
        inst_payload = {
            "nombre_instancia": "XEPDB1",
            "puerto": 1521,
            "id_servidor": self.ids["id_servidor"],
            "id_dbms": self.ids["id_dbms_oracle"],
            "id_estado_instancia": self.ids["id_estado"]
        }
        res = self.client.post("/sgir/v1/crud/instancias/", json=inst_payload, headers=self.headers)
        if res.status_code == 201:
            self.__class__.ids["id_instancia"] = res.json()["id_instancia"]
        else:
            # Buscar preexistente
            list_res = self.client.get(f"/sgir/v1/crud/instancias/servidor/{self.ids['id_servidor']}", headers=self.headers)
            for inst in list_res.json():
                if inst["nombre_instancia"] == "XEPDB1":
                    self.__class__.ids["id_instancia"] = inst["id_instancia"]
                    break

        self.assertIsNotNone(self.ids["id_instancia"], "Debe existir la instancia de base de datos Oracle.")
        print(f"[TEST] Target Oracle configurado -> Servidor ID: {self.ids['id_servidor']}, Credencial ID: {self.ids['id_credencial']}, Instancia ID: {self.ids['id_instancia']}")

    def test_04_monitoring_bajo_criticidad(self):
        """4. Monitoreo Bajo (Grupo A): Actualiza a Bajo y verifica que solo retorne conectividad (Grupo A)."""
        self.assertIsNotNone(self.ids["id_servidor"])
        
        # A. Actualizar criticidad del servidor a Bajo
        bajo_id = self.criticidad_ids["Bajo"]
        upd_res = self.client.put(
            f"/sgir/v1/crud/servidores/{self.ids['id_servidor']}",
            json={"id_nivel_criticidad": bajo_id},
            headers=self.headers
        )
        self.assertEqual(upd_res.status_code, 200, "Error al actualizar criticidad a Bajo")
        print("\n--- [PROBANDO GRUPO A: CRITICIDAD BAJA (MONITOREANDO POR 5 SEGUNDOS)] ---")

        for i in range(1, 6):
            start_time = time.time()
            mon_res = self.client.get(
                f"/sgir/v1/m1/oracle/{self.ids['id_instancia']}/{self.ids['id_credencial']}",
                headers=self.headers
            )
            
            if mon_res.status_code == 200:
                data = mon_res.json()
                print(f"\n⏱️ [Segundo {i}] Respuesta recibida (Bajo):")
                print(json.dumps(data, indent=2, ensure_ascii=False))
                
                # Comprobaciones de Grupos
                self.assertEqual(data["nivel_criticidad"].lower(), "bajo")
                self.assertIsNotNone(data.get("grupo_a"), "El Grupo A (Conectividad) debe estar presente.")
                self.assertIsNone(data.get("grupo_b"), "El Grupo B (Recursos) debe ser null para criticidad Bajo.")
                self.assertIsNone(data.get("grupo_c"), "El Grupo C (Performance) debe ser null para criticidad Bajo.")
            else:
                self.fail(f"[ERROR] Código de estado {mon_res.status_code}: {mon_res.text}")
                
            elapsed = time.time() - start_time
            sleep_time = max(0.1, 1.0 - elapsed)
            if i < 5:
                time.sleep(sleep_time)

    def test_05_monitoring_medio_criticidad(self):
        """5. Monitoreo Medio (Grupos A+B): Actualiza a Medio y verifica conectividad y recursos."""
        self.assertIsNotNone(self.ids["id_servidor"])
        
        # A. Actualizar criticidad del servidor a Medio
        medio_id = self.criticidad_ids["Medio"]
        upd_res = self.client.put(
            f"/sgir/v1/crud/servidores/{self.ids['id_servidor']}",
            json={"id_nivel_criticidad": medio_id},
            headers=self.headers
        )
        self.assertEqual(upd_res.status_code, 200, "Error al actualizar criticidad a Medio")
        print("\n--- [PROBANDO GRUPOS A+B: CRITICIDAD MEDIA (MONITOREANDO POR 5 SEGUNDOS)] ---")

        for i in range(1, 6):
            start_time = time.time()
            mon_res = self.client.get(
                f"/sgir/v1/m1/oracle/{self.ids['id_instancia']}/{self.ids['id_credencial']}",
                headers=self.headers
            )
            
            if mon_res.status_code == 200:
                data = mon_res.json()
                print(f"\n⏱️ [Segundo {i}] Respuesta recibida (Medio):")
                print(json.dumps(data, indent=2, ensure_ascii=False))
                
                # Comprobaciones de Grupos
                self.assertEqual(data["nivel_criticidad"].lower(), "medio")
                self.assertIsNotNone(data.get("grupo_a"), "El Grupo A (Conectividad) debe estar presente.")
                self.assertIsNotNone(data.get("grupo_b"), "El Grupo B (Recursos) debe estar presente para criticidad Medio.")
                self.assertIsNone(data.get("grupo_c"), "El Grupo C (Performance) debe ser null para criticidad Medio.")
            else:
                self.fail(f"[ERROR] Código de estado {mon_res.status_code}: {mon_res.text}")
                
            elapsed = time.time() - start_time
            sleep_time = max(0.1, 1.0 - elapsed)
            if i < 5:
                time.sleep(sleep_time)

    def test_06_monitoring_alto_criticidad(self):
        """6. Monitoreo Alto (Grupos A+B+C): Actualiza a Alto y verifica el monitoreo completo."""
        self.assertIsNotNone(self.ids["id_servidor"])
        
        # A. Actualizar criticidad del servidor a Alto
        alto_id = self.criticidad_ids["Alto"]
        upd_res = self.client.put(
            f"/sgir/v1/crud/servidores/{self.ids['id_servidor']}",
            json={"id_nivel_criticidad": alto_id},
            headers=self.headers
        )
        self.assertEqual(upd_res.status_code, 200, "Error al actualizar criticidad a Alto")
        print("\n--- [PROBANDO GRUPOS A+B+C: CRITICIDAD ALTA (MONITOREANDO POR 5 SEGUNDOS)] ---")

        for i in range(1, 6):
            start_time = time.time()
            mon_res = self.client.get(
                f"/sgir/v1/m1/oracle/{self.ids['id_instancia']}/{self.ids['id_credencial']}",
                headers=self.headers
            )
            
            if mon_res.status_code == 200:
                data = mon_res.json()
                print(f"\n⏱️ [Segundo {i}] Respuesta recibida (Alto):")
                print(json.dumps(data, indent=2, ensure_ascii=False))
                
                # Comprobaciones de Grupos
                self.assertEqual(data["nivel_criticidad"].lower(), "alto")
                self.assertIsNotNone(data.get("grupo_a"), "El Grupo A (Conectividad) debe estar presente.")
                self.assertIsNotNone(data.get("grupo_b"), "El Grupo B (Recursos) debe estar presente para criticidad Alto.")
                self.assertIsNotNone(data.get("grupo_c"), "El Grupo C (Performance) debe estar presente para criticidad Alto.")
            else:
                self.fail(f"[ERROR] Código de estado {mon_res.status_code}: {mon_res.text}")
                
            elapsed = time.time() - start_time
            sleep_time = max(0.1, 1.0 - elapsed)
            if i < 5:
                time.sleep(sleep_time)

if __name__ == "__main__":
    unittest.main()
