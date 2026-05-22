import unittest
import httpx
import time

class TestDBLiveCache(unittest.TestCase):
    # Bandera configurable para activar el APScheduler en segundo plano durante el test
    ACTIVATE_SCHEDULER = True

    @classmethod
    def setUpClass(cls):
        cls.base_url = "http://localhost:8000"
        cls.client = httpx.Client(base_url=cls.base_url)
        cls.token = None
        cls.headers = {}
        cls.mysql_instance_id = None
        cls.mysql_credential_id = None
        
        # Catálogos base de respaldo
        cls.catalog_ids = {
            "id_estado": 1,
            "id_criticidad": 1,
            "id_acceso_db": 2,
            "dbms": {
                "mysql8": 3
            }
        }

    @classmethod
    def tearDownClass(cls):
        cls.client.close()

    def test_01_login_and_setup_mysql(self):
        """1. Autenticación y Registro: Inicia sesión, resuelve catálogos y asegura el container MySQL 8."""
        # A. Login
        login_payload = {
            "username": "admin@admin.com",
            "password": "123Nokia"
        }
        response = self.client.post("/sgir/v1/crud/users/login", data=login_payload)
        self.assertEqual(response.status_code, 200, "Fallo al iniciar sesión. Verifica el estado del backend.")
        
        token_data = response.json()
        self.assertIn("access_token", token_data)
        self.__class__.token = token_data["access_token"]
        self.__class__.headers = {"Authorization": f"Bearer {self.token}"}
        print("\n🔑 [TEST] Sesión iniciada correctamente como Administrador.")

        # B. Resolver catálogos del sistema
        # Estado Activo
        res = self.client.get("/sgir/v1/crud/estados/", headers=self.headers)
        if res.status_code == 200 and res.json():
            self.__class__.catalog_ids["id_estado"] = res.json()[0]["id_estado"]
        
        # Criticidad
        res = self.client.get("/sgir/v1/crud/criticidad/", headers=self.headers)
        if res.status_code == 200 and res.json():
            self.__class__.catalog_ids["id_criticidad"] = res.json()[0]["id_nivel_criticidad"]

        # Tipo de Acceso Native/DB
        res = self.client.get("/sgir/v1/crud/tipo-acceso/", headers=self.headers)
        if res.status_code == 200 and res.json():
            for access in res.json():
                if "native" in access["nombre_tipo"].lower() or "db" in access["nombre_tipo"].lower():
                    self.__class__.catalog_ids["id_acceso_db"] = access["id_tipo_acceso"]
                    break

        print(f"📋 [TEST] Catálogos resueltos -> Estado: {self.catalog_ids['id_estado']}, Criticidad: {self.catalog_ids['id_criticidad']}, Acceso DB: {self.catalog_ids['id_acceso_db']}")

        # C. Registrar el servidor de MySQL 8
        srv_id = self._get_or_create_server("sgir_mysql8", "127.0.0.1", "Contenedor de pruebas MySQL 8.0")
        
        # D. Registrar credencial de DB Native
        self.__class__.mysql_credential_id = self._get_or_create_credential(
            "sgir", "sgir", self.catalog_ids["id_acceso_db"], srv_id
        )
        self.assertIsNotNone(self.mysql_credential_id, "Error al registrar credenciales para MySQL 8.")
        
        # E. Registrar instancia DBMS (MySQL 8, Puerto 3308, DBMS ID 3)
        self.__class__.mysql_instance_id = self._get_or_create_instance(
            "sgir_db_8", 3308, srv_id, self.catalog_ids["dbms"]["mysql8"]
        )
        self.assertIsNotNone(self.mysql_instance_id, "Error al registrar la instancia de MySQL 8.")
        print(f"🐳 [TEST] Instancia MySQL 8 registrada -> ID: {self.mysql_instance_id}, Credencial ID: {self.mysql_credential_id}")

    def _get_or_create_server(self, name: str, ip: str, description: str) -> int:
        """Helper para registrar o recuperar el servidor (soporta IP de red del contenedor)."""
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
            return res.json()["id_servidor"]
        else:
            list_res = self.client.get("/sgir/v1/crud/servidores/", headers=self.headers)
            if list_res.status_code == 200:
                for srv in list_res.json():
                    if srv["nombre_servidor"] == name:
                        # Si la IP preexistente es local, la actualizamos para que funcione dentro de Docker
                        if srv["direccion_ip"] in ["127.0.0.1", "localhost"]:
                            self.client.put(
                                f"/sgir/v1/crud/servidores/{srv['id_servidor']}",
                                json={"direccion_ip": resolved_ip},
                                headers=self.headers
                            )
                        return srv["id_servidor"]
            raise Exception(f"Error al resolver el servidor '{name}': {res.text}")

    def _get_or_create_credential(self, user: str, password: str, access_type: int, server_id: int) -> int:
        """Helper para registrar o recuperar la credencial de base de datos."""
        payload = {
            "usuario": user,
            "password": password,
            "id_tipo_acceso": access_type,
            "id_estado_credencial": self.catalog_ids["id_estado"],
            "id_servidor": server_id
        }
        res = self.client.post("/sgir/v1/crud/credenciales/", json=payload, headers=self.headers)
        if res.status_code == 201:
            return res.json()["id_credencial"]
        else:
            list_res = self.client.get(f"/sgir/v1/crud/credenciales/servidor/{server_id}", headers=self.headers)
            if list_res.status_code == 200:
                for cred in list_res.json():
                    if cred["usuario"] == user and cred["id_tipo_acceso"] == access_type:
                        return cred["id_credencial"]
            raise Exception(f"Error al resolver credenciales para '{user}': {res.text}")

    def _get_or_create_instance(self, name: str, port: int, server_id: int, dbms_id: int) -> int:
        """Helper para registrar o recuperar la instancia de base de datos."""
        payload = {
            "nombre_instancia": name,
            "puerto": port,
            "id_servidor": server_id,
            "id_dbms": dbms_id,
            "id_estado_instancia": self.catalog_ids["id_estado"]
        }
        res = self.client.post("/sgir/v1/crud/instancias/", json=payload, headers=self.headers)
        if res.status_code == 201:
            return res.json()["id_instancia"]
        else:
            list_res = self.client.get(f"/sgir/v1/crud/instancias/servidor/{server_id}", headers=self.headers)
            if list_res.status_code == 200:
                for inst in list_res.json():
                    if inst["nombre_instancia"] == name:
                        return inst["id_instancia"]
            raise Exception(f"Error al resolver la instancia '{name}': {res.text}")

    def test_02_apscheduler_toggle(self):
        """2. Control de APScheduler: Activa o desactiva el scheduler según la bandera ACTIVATE_SCHEDULER."""
        self.assertIsNotNone(self.token)
        # Llamamos al helper de apoyo pasándole la bandera configurada
        self.run_apscheduler_toggle(self.ACTIVATE_SCHEDULER)

    def run_apscheduler_toggle(self, activate: bool):
        """Helper de apoyo interno (sin prefijo test_) para activar/pausar de forma segura el APScheduler."""
        self.assertIsNotNone(self.token)
        
        if activate:
            print(f"\n⏰ [SCHEDULER] Activando específicamente el APScheduler (Param: {activate})...")
            resume_res = self.client.post("/sgir/v1/m1/host/scheduler/resume", headers=self.headers)
            self.assertEqual(resume_res.status_code, 200, f"Error al reanudar: {resume_res.text}")
            
            # Verificar estado reanudado
            status_res = self.client.get("/sgir/v1/m1/host/scheduler/status", headers=self.headers)
            self.assertEqual(status_res.status_code, 200)
            self.assertEqual(status_res.json()["status"], "running", "El scheduler debería estar en ejecución.")
            
            print("⏳ [SCHEDULER] Esperando 3 segundos para el flujo en segundo plano...")
            time.sleep(3)
        else:
            print(f"\n🔕 [SCHEDULER] Pausando/Desactivando específicamente el APScheduler (Param: {activate})...")
            pause_res = self.client.post("/sgir/v1/m1/host/scheduler/pause", headers=self.headers)
            self.assertEqual(pause_res.status_code, 200, f"Error al pausar: {pause_res.text}")
            
            # Verificar estado pausado
            status_res = self.client.get("/sgir/v1/m1/host/scheduler/status", headers=self.headers)
            self.assertEqual(status_res.status_code, 200)
            self.assertEqual(status_res.json()["status"], "paused", "El scheduler debería estar pausado.")

        # Disparamos un monitoreo ad-hoc instantáneo para asegurar que el caché siempre esté poblado
        # con métricas frescas del contenedor, sin importar los intervalos largos del scheduler.
        print("🚀 [TEST] Disparando monitoreo ad-hoc para poblar el caché en tiempo real de MySQL 8...")
        adhoc_res = self.client.post(
            f"/sgir/v1/m1/db/run-adhoc/{self.mysql_instance_id}/{self.mysql_credential_id}",
            headers=self.headers
        )
        self.assertEqual(adhoc_res.status_code, 200, f"Error en monitoreo adhoc: {adhoc_res.text}")

    def test_03_get_live_cache_endpoint(self):
        """3. Cache Real-time: Obtiene y valida el caché comprimido/estructurado global."""
        self.assertIsNotNone(self.token)
        
        response = self.client.get("/sgir/v1/m1/db/live-cache", headers=self.headers)
        self.assertEqual(response.status_code, 200, f"Error al consultar live-cache: {response.text}")
        
        cache_data = response.json()
        self.assertIsInstance(cache_data, dict, "El caché debe ser un diccionario indexado por ID de instancia.")
        print(f"\n📦 [TEST] Caché global recibido. Elementos registrados: {len(cache_data)}")

        # Comprobar que la instancia de MySQL 8 esté presente en el caché
        str_inst_id = str(self.mysql_instance_id)
        self.assertIn(str_inst_id, cache_data, f"La instancia de MySQL 8 (ID {str_inst_id}) debería estar en el live-cache.")

        # Validar el formato de los elementos (soporta tanto piped string del scheduler como dict estructurado del adhoc)
        for inst_id, cache_val in cache_data.items():
            if isinstance(cache_val, dict):
                # Formato diccionario (monitoreo ad-hoc/unificado)
                self.assertIn("engine", cache_val)
                self.assertIn("metrics", cache_val)
                metrics = cache_val["metrics"]
                self.assertIn("ping", metrics)
                self.assertIn("capacity_pct", metrics)
                print(f"   ✅ Instancia ID {inst_id} validada (Dict) -> Engine: {cache_val['engine']} | Ping: {metrics['ping']}")
            else:
                # Formato piped string (monitoreo programado bulk)
                self.assertIsInstance(cache_val, str)
                parts = cache_val.split('|')
                self.assertEqual(len(parts), 15, f"La cadena de la instancia {inst_id} debe tener 15 campos. Recibido: {cache_val}")
                
                status = parts[0]
                conn_usage_percent = parts[4]
                print(f"   ✅ Instancia ID {inst_id} validada (Piped) -> Status: {status} | Uso Conexiones: {conn_usage_percent}%")

    def test_04_get_health_status_compatibility(self):
        """4. Compatibilidad: Valida el parseo retrocompatible de la caché comprimida/estructurada usando MySQL 8."""
        self.assertIsNotNone(self.token)
        self.assertIsNotNone(self.mysql_instance_id)
        
        # Consultar salud unificada clásica de la DB para nuestra instancia MySQL 8
        response_health = self.client.get(f"/sgir/v1/m1/db/health-status/{self.mysql_instance_id}", headers=self.headers)
        self.assertEqual(response_health.status_code, 200, f"Error al consultar compatibilidad de health-status: {response_health.text}")
        
        health_data = response_health.json()
        self.assertIn("status", health_data)
        self.assertIn("engine", health_data)
        self.assertIn("metrics", health_data)
        
        metrics = health_data["metrics"]
        self.assertIn("ping", metrics)
        self.assertIn("capacity_pct", metrics)
        self.assertIn("stuck_processes", metrics)
        self.assertIn("specific_value", metrics)
        
        print(f"\n🧩 [TEST] Compatibilidad retroactiva validada con éxito para MySQL 8 (ID {self.mysql_instance_id}).")
        print(f"   Resultado -> Estado Salud: {health_data['status']} | Motor: {health_data['engine']} | Ping: {metrics['ping']}ms | Capacidad: {metrics['capacity_pct']}%")

if __name__ == "__main__":
    unittest.main()
