import unittest
import httpx
import uuid

class TestCrudInsert(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.base_url = "http://localhost:8000"
        cls.client = httpx.Client(base_url=cls.base_url)
        cls.token = None
        cls.headers = {}
        
        # IDs que se irán recuperando y propagando en cascada
        cls.ids = {
            "id_estado": 1,
            "id_criticidad": 1,
            "id_tipo_acceso": 1,
            "id_dbms": 1,
            "id_tipo_respaldo": 1,
            "id_tipo_almacenamiento": 1,
            "id_nivel_alerta": 1,
            "id_tipo_metrica": 1,
            "id_tipo_evento": 1,
            "id_servidor": None,
            "id_particion": None,
            "id_credencial": None,
            "id_instancia": None,
            "id_base_datos": None,
            "id_ruta_respaldo": None,
            "id_politica": None,
            "id_respaldo": None,
            "id_monitoreo": None,
            "id_metrica": None,
            "id_alerta": None
        }
        
        # Generar un sufijo único para evitar colisiones de nombres únicos
        cls.suffix = uuid.uuid4().hex[:6]

    @classmethod
    def tearDownClass(cls):
        cls.client.close()

    def test_01_login(self):
        """1. Autenticación (Login): Obtiene el token JWT usando el usuario administrador base."""
        login_payload = {
            "username": "admin@admin.com",
            "password": "123Nokia"
        }
        response = self.client.post("/sgir/v1/crud/users/login", data=login_payload)
        
        self.assertEqual(response.status_code, 200, "Error al autenticarse. Asegúrate de haber ejecutado 00_base.py")
        token_data = response.json()
        self.assertIn("access_token", token_data)
        
        self.__class__.token = token_data["access_token"]
        self.__class__.headers = {"Authorization": f"Bearer {self.token}"}
        print("\n[LOGIN SUCCESS] Token JWT recibido correctamente.")

    def test_02_create_catalogs(self):
        """2. Catálogos Base: Asegura e inserta/obtiene IDs para todos los catálogos base."""
        # Se requiere token
        self.assertIsNotNone(self.token, "Se requiere estar autenticado para crear catálogos.")

        # --- A. Estado General ---
        estado_payload = {"nombre_estado": f"TEST_ESTADO_{self.suffix}"}
        res = self.client.post("/sgir/v1/crud/estados/", json=estado_payload, headers=self.headers)
        if res.status_code == 201:
            self.__class__.ids["id_estado"] = res.json()["id_estado"]
            print(f"[CATALOGO] Estado creado ID: {self.ids['id_estado']}")
        else:
            list_res = self.client.get("/sgir/v1/crud/estados/", headers=self.headers)
            if list_res.status_code == 200 and list_res.json():
                self.__class__.ids["id_estado"] = list_res.json()[0]["id_estado"]
                print(f"[CATALOGO] Estado preexistente fallback ID: {self.ids['id_estado']}")

        # --- B. Nivel Criticidad ---
        criticidad_payload = {"nombre_nivel": f"TEST_CRITICIDAD_{self.suffix}", "descripcion": "Prueba"}
        res = self.client.post("/sgir/v1/crud/criticidad/", json=criticidad_payload, headers=self.headers)
        if res.status_code == 201:
            self.__class__.ids["id_criticidad"] = res.json()["id_nivel_criticidad"]
            print(f"[CATALOGO] Criticidad creada ID: {self.ids['id_criticidad']}")
        else:
            list_res = self.client.get("/sgir/v1/crud/criticidad/", headers=self.headers)
            if list_res.status_code == 200 and list_res.json():
                self.__class__.ids["id_criticidad"] = list_res.json()[0]["id_nivel_criticidad"]
                print(f"[CATALOGO] Criticidad preexistente fallback ID: {self.ids['id_criticidad']}")

        # --- C. Tipo Acceso ---
        acceso_payload = {"nombre_tipo": f"TEST_ACCESO_{self.suffix}"}
        res = self.client.post("/sgir/v1/crud/tipo-acceso/", json=acceso_payload, headers=self.headers)
        if res.status_code == 201:
            self.__class__.ids["id_tipo_acceso"] = res.json()["id_tipo_acceso"]
            print(f"[CATALOGO] Tipo Acceso creado ID: {self.ids['id_tipo_acceso']}")
        else:
            list_res = self.client.get("/sgir/v1/crud/tipo-acceso/", headers=self.headers)
            if list_res.status_code == 200 and list_res.json():
                self.__class__.ids["id_tipo_acceso"] = list_res.json()[0]["id_tipo_acceso"]
                print(f"[CATALOGO] Tipo Acceso preexistente fallback ID: {self.ids['id_tipo_acceso']}")

        # --- D. DBMS ---
        dbms_payload = {"nombre_dbms": f"TEST_DBMS_{self.suffix}", "version": "1.0", "descripcion": "Prueba"}
        res = self.client.post("/sgir/v1/crud/dbms/", json=dbms_payload, headers=self.headers)
        if res.status_code == 201:
            self.__class__.ids["id_dbms"] = res.json()["id_dbms"]
            print(f"[CATALOGO] DBMS creado ID: {self.ids['id_dbms']}")
        else:
            list_res = self.client.get("/sgir/v1/crud/dbms/", headers=self.headers)
            if list_res.status_code == 200 and list_res.json():
                self.__class__.ids["id_dbms"] = list_res.json()[0]["id_dbms"]
                print(f"[CATALOGO] DBMS preexistente fallback ID: {self.ids['id_dbms']}")

        # --- E. Tipo Respaldo ---
        tipo_respaldo_payload = {"nombre_tipo": f"TEST_TIPO_RESP_{self.suffix}"}
        res = self.client.post("/sgir/v1/crud/tipo-respaldo/", json=tipo_respaldo_payload, headers=self.headers)
        if res.status_code == 201:
            self.__class__.ids["id_tipo_respaldo"] = res.json()["id_tipo_respaldo"]
            print(f"[CATALOGO] Tipo Respaldo creado ID: {self.ids['id_tipo_respaldo']}")
        else:
            list_res = self.client.get("/sgir/v1/crud/tipo-respaldo/", headers=self.headers)
            if list_res.status_code == 200 and list_res.json():
                self.__class__.ids["id_tipo_respaldo"] = list_res.json()[0]["id_tipo_respaldo"]
                print(f"[CATALOGO] Tipo Respaldo preexistente fallback ID: {self.ids['id_tipo_respaldo']}")

        # --- F. Tipo Almacenamiento ---
        tipo_almacenamiento_payload = {"nombre_tipo": f"TEST_TIPO_ALM_{self.suffix}"}
        res = self.client.post("/sgir/v1/crud/tipo-almacenamiento/", json=tipo_almacenamiento_payload, headers=self.headers)
        if res.status_code == 201:
            self.__class__.ids["id_tipo_almacenamiento"] = res.json()["id_tipo_almacenamiento"]
            print(f"[CATALOGO] Tipo Almacenamiento creado ID: {self.ids['id_tipo_almacenamiento']}")
        else:
            list_res = self.client.get("/sgir/v1/crud/tipo-almacenamiento/", headers=self.headers)
            if list_res.status_code == 200 and list_res.json():
                self.__class__.ids["id_tipo_almacenamiento"] = list_res.json()[0]["id_tipo_almacenamiento"]
                print(f"[CATALOGO] Tipo Almacenamiento preexistente fallback ID: {self.ids['id_tipo_almacenamiento']}")

        # --- G. Nivel Alerta ---
        nivel_alerta_payload = {"nombre_nivel": f"TEST_NIVEL_AL_{self.suffix}"}
        res = self.client.post("/sgir/v1/crud/nivel-alerta/", json=nivel_alerta_payload, headers=self.headers)
        if res.status_code == 201:
            self.__class__.ids["id_nivel_alerta"] = res.json()["id_nivel_alerta"]
            print(f"[CATALOGO] Nivel Alerta creado ID: {self.ids['id_nivel_alerta']}")
        else:
            list_res = self.client.get("/sgir/v1/crud/nivel-alerta/", headers=self.headers)
            if list_res.status_code == 200 and list_res.json():
                self.__class__.ids["id_nivel_alerta"] = list_res.json()[0]["id_nivel_alerta"]
                print(f"[CATALOGO] Nivel Alerta preexistente fallback ID: {self.ids['id_nivel_alerta']}")

        # --- H. Tipo Métrica ---
        tipo_metrica_payload = {"nombre_tipo": f"TEST_METRICA_{self.suffix}", "unidad_medida": "%"}
        res = self.client.post("/sgir/v1/crud/tipo-metrica/", json=tipo_metrica_payload, headers=self.headers)
        if res.status_code == 201:
            self.__class__.ids["id_tipo_metrica"] = res.json()["id_tipo_metrica"]
            print(f"[CATALOGO] Tipo Metrica creado ID: {self.ids['id_tipo_metrica']}")
        else:
            list_res = self.client.get("/sgir/v1/crud/tipo-metrica/", headers=self.headers)
            if list_res.status_code == 200 and list_res.json():
                self.__class__.ids["id_tipo_metrica"] = list_res.json()[0]["id_tipo_metrica"]
                print(f"[CATALOGO] Tipo Metrica preexistente fallback ID: {self.ids['id_tipo_metrica']}")

        # --- I. Tipo Evento Auditoría ---
        tipo_evento_payload = {"nombre_evento": f"TEST_EVENTO_{self.suffix}"}
        res = self.client.post("/sgir/v1/crud/audit-types/", json=tipo_evento_payload, headers=self.headers)
        if res.status_code == 201:
            self.__class__.ids["id_tipo_evento"] = res.json()["id_tipo_evento"]
            print(f"[CATALOGO] Tipo Evento creado ID: {self.ids['id_tipo_evento']}")
        else:
            list_res = self.client.get("/sgir/v1/crud/audit-types/", headers=self.headers)
            if list_res.status_code == 200 and list_res.json():
                self.__class__.ids["id_tipo_evento"] = list_res.json()[0]["id_tipo_evento"]
                print(f"[CATALOGO] Tipo Evento preexistente fallback ID: {self.ids['id_tipo_evento']}")

    def test_03_insert_servidor(self):
        """3. Servidor: Inserta un nuevo servidor en la base de datos."""
        self.assertIsNotNone(self.token)
        
        servidor_payload = {
            "nombre_servidor": f"srv-test-{self.suffix}",
            "direccion_ip": "10.0.0.99",
            "es_legacy": False,
            "descripcion": "Servidor de integración de pruebas CRUD",
            "monitoreo_host": True,
            "monitoreo_db": True,
            "id_nivel_criticidad": self.ids["id_criticidad"],
            "id_estado_servidor": self.ids["id_estado"]
        }
        
        response = self.client.post("/sgir/v1/crud/servidores/", json=servidor_payload, headers=self.headers)
        self.assertEqual(response.status_code, 201, f"Error al insertar servidor: {response.text}")
        data = response.json()
        self.assertIn("id_servidor", data)
        self.__class__.ids["id_servidor"] = data["id_servidor"]
        print(f"\n[INSERT SUCCESS] Servidor creado con ID: {data['id_servidor']}")

    def test_04_insert_servidor_particion(self):
        """4. Servidor Particion: Vincula una partición al servidor creado."""
        self.assertIsNotNone(self.ids["id_servidor"], "Se requiere el servidor para agregar una partición.")
        
        particion_payload = {
            "id_servidor": self.ids["id_servidor"],
            "path": f"/mnt/disk-{self.suffix}",
            "etiqueta": "disk_test"
        }
        
        response = self.client.post("/sgir/v1/crud/particiones/", json=particion_payload, headers=self.headers)
        self.assertEqual(response.status_code, 201, f"Error al insertar partición: {response.text}")
        data = response.json()
        self.assertIn("id_particion", data)
        self.__class__.ids["id_particion"] = data["id_particion"]
        print(f"[INSERT SUCCESS] Partición creada con ID: {data['id_particion']} en servidor {self.ids['id_servidor']}")

    def test_05_insert_credencial_acceso(self):
        """5. Credencial de Acceso: Agrega credenciales asociadas al servidor."""
        self.assertIsNotNone(self.ids["id_servidor"])
        
        credencial_payload = {
            "usuario": f"user_{self.suffix}",
            "password": "PasswordTest123",
            "id_tipo_acceso": self.ids["id_tipo_acceso"],
            "id_estado_credencial": self.ids["id_estado"],
            "id_servidor": self.ids["id_servidor"]
        }
        
        response = self.client.post("/sgir/v1/crud/credenciales/", json=credencial_payload, headers=self.headers)
        self.assertEqual(response.status_code, 201, f"Error al insertar credencial: {response.text}")
        data = response.json()
        self.assertIn("id_credencial", data)
        self.__class__.ids["id_credencial"] = data["id_credencial"]
        print(f"[INSERT SUCCESS] Credencial creada con ID: {data['id_credencial']}")

    def test_06_insert_instancia_dbms(self):
        """6. Instancia DBMS: Crea una instancia en el servidor."""
        self.assertIsNotNone(self.ids["id_servidor"])
        
        instancia_payload = {
            "nombre_instancia": f"inst-{self.suffix}",
            "puerto": 5433,
            "id_servidor": self.ids["id_servidor"],
            "id_dbms": self.ids["id_dbms"],
            "id_estado_instancia": self.ids["id_estado"]
        }
        
        response = self.client.post("/sgir/v1/crud/instancias/", json=instancia_payload, headers=self.headers)
        self.assertEqual(response.status_code, 201, f"Error al insertar instancia DBMS: {response.text}")
        data = response.json()
        self.assertIn("id_instancia", data)
        self.__class__.ids["id_instancia"] = data["id_instancia"]
        print(f"[INSERT SUCCESS] Instancia DBMS creada con ID: {data['id_instancia']}")

    def test_07_insert_base_de_datos(self):
        """7. Base de Datos: Registra una base de datos dentro de la instancia."""
        self.assertIsNotNone(self.ids["id_instancia"])
        
        bd_payload = {
            "nombre_base": f"db_{self.suffix}",
            "tamano_mb": 250.0,
            "id_instancia": self.ids["id_instancia"],
            "id_estado_bd": self.ids["id_estado"]
        }
        
        response = self.client.post("/sgir/v1/crud/bases-de-datos/", json=bd_payload, headers=self.headers)
        self.assertEqual(response.status_code, 201, f"Error al insertar base de datos: {response.text}")
        data = response.json()
        self.assertIn("id_base_datos", data)
        self.__class__.ids["id_base_datos"] = data["id_base_datos"]
        print(f"[INSERT SUCCESS] Base de Datos creada con ID: {data['id_base_datos']}")

    def test_08_insert_ruta_respaldo(self):
        """8. Ruta de Respaldo: Registra una ruta para backups en el servidor."""
        self.assertIsNotNone(self.ids["id_servidor"])
        
        ruta_payload = {
            "descripcion_ruta": f"Ruta backup test {self.suffix}",
            "path": f"/var/backups/{self.suffix}",
            "id_servidor": self.ids["id_servidor"],
            "id_tipo_almacenamiento": self.ids["id_tipo_almacenamiento"],
            "id_estado_ruta": self.ids["id_estado"]
        }
        
        response = self.client.post("/sgir/v1/crud/rutas-respaldo/", json=ruta_payload, headers=self.headers)
        self.assertEqual(response.status_code, 201, f"Error al crear ruta de respaldo: {response.text}")
        data = response.json()
        self.assertIn("id_ruta", data)
        self.__class__.ids["id_ruta_respaldo"] = data["id_ruta"]
        print(f"[INSERT SUCCESS] Ruta de Respaldo creada con ID: {data['id_ruta']}")

    def test_09_insert_politica_respaldo(self):
        """9. Política de Respaldo: Agrega una nueva política."""
        politica_payload = {
            "nombre_politica": f"politica-diaria-{self.suffix}",
            "descripcion": "Copia diaria automatizada",
            "frecuencia_horas": 24,
            "retencion_dias": 7,
            "id_tipo_respaldo": self.ids["id_tipo_respaldo"],
            "id_estado_politica": self.ids["id_estado"]
        }
        
        response = self.client.post("/sgir/v1/crud/politicas-respaldo/", json=politica_payload, headers=self.headers)
        self.assertEqual(response.status_code, 201, f"Error al crear política de respaldo: {response.text}")
        data = response.json()
        self.assertIn("id_politica", data)
        self.__class__.ids["id_politica"] = data["id_politica"]
        print(f"[INSERT SUCCESS] Política de Respaldo creada con ID: {data['id_politica']}")

    def test_10_assign_policy_to_db(self):
        """10. Asignación de Política: Vincula la política a la base de datos."""
        self.assertIsNotNone(self.ids["id_base_datos"])
        self.assertIsNotNone(self.ids["id_politica"])
        
        asignacion_payload = {
            "id_base_datos": self.ids["id_base_datos"],
            "id_politica": self.ids["id_politica"]
        }
        
        response = self.client.post("/sgir/v1/crud/asignacion-politica/", json=asignacion_payload, headers=self.headers)
        self.assertEqual(response.status_code, 201, f"Error en asignación de política: {response.text}")
        print(f"[INSERT SUCCESS] Política {self.ids['id_politica']} asignada a BD {self.ids['id_base_datos']}")

    def test_11_insert_respaldo(self):
        """11. Respaldo: Registra el histórico de una ejecución de backup."""
        self.assertIsNotNone(self.ids["id_base_datos"])
        self.assertIsNotNone(self.ids["id_politica"])
        self.assertIsNotNone(self.ids["id_credencial"])
        self.assertIsNotNone(self.ids["id_ruta_respaldo"])
        
        respaldo_payload = {
            "fecha_inicio": "2026-05-19T14:00:00Z",
            "fecha_fin": "2026-05-19T14:05:00Z",
            "tamano_mb": 185.7,
            "hash_integridad": "5d41402abc4b2a76b9719d911017c592",
            "id_base_datos": self.ids["id_base_datos"],
            "id_politica": self.ids["id_politica"],
            "id_credencial": self.ids["id_credencial"],
            "id_ruta_respaldo": self.ids["id_ruta_respaldo"],
            "id_estado_ejecucion": self.ids["id_estado"]
        }
        
        response = self.client.post("/sgir/v1/crud/respaldos/", json=respaldo_payload, headers=self.headers)
        self.assertEqual(response.status_code, 201, f"Error al registrar ejecución de respaldo: {response.text}")
        data = response.json()
        self.assertIn("id_respaldo", data)
        self.__class__.ids["id_respaldo"] = data["id_respaldo"]
        print(f"[INSERT SUCCESS] Respaldo registrado con ID: {data['id_respaldo']}")

    def test_12_insert_monitoreo(self):
        """12. Sesión de Monitoreo: Inicia una sesión de monitoreo."""
        self.assertIsNotNone(self.ids["id_servidor"])
        
        monitoreo_payload = {
            "id_servidor": self.ids["id_servidor"],
            "id_estado_monitoreo": self.ids["id_estado"]
        }
        
        response = self.client.post("/sgir/v1/crud/monitoreo/", json=monitoreo_payload, headers=self.headers)
        self.assertEqual(response.status_code, 201, f"Error al iniciar monitoreo: {response.text}")
        data = response.json()
        self.assertIn("id_monitoreo", data)
        self.__class__.ids["id_monitoreo"] = data["id_monitoreo"]
        print(f"[INSERT SUCCESS] Sesión de Monitoreo creada con ID: {data['id_monitoreo']}")

    def test_13_insert_metrica(self):
        """13. Métrica: Registra una métrica en la sesión de monitoreo."""
        self.assertIsNotNone(self.ids["id_monitoreo"])
        
        metrica_payload = {
            "valor": 65.5,
            "id_monitoreo": self.ids["id_monitoreo"],
            "id_tipo_metrica": self.ids["id_tipo_metrica"]
        }
        
        response = self.client.post("/sgir/v1/crud/metricas/", json=metrica_payload, headers=self.headers)
        self.assertEqual(response.status_code, 201, f"Error al registrar métrica: {response.text}")
        data = response.json()
        self.assertIn("id_metrica", data)
        self.__class__.ids["id_metrica"] = data["id_metrica"]
        print(f"[INSERT SUCCESS] Métrica registrada con ID: {data['id_metrica']}")

    def test_14_insert_alerta(self):
        """14. Alerta: Genera una alerta de prueba asociada al servidor."""
        self.assertIsNotNone(self.ids["id_servidor"])
        
        alerta_payload = {
            "descripcion": "Uso excesivo de CPU detectado en pruebas de inserción",
            "id_servidor": self.ids["id_servidor"],
            "id_monitoreo": self.ids["id_monitoreo"],
            "id_nivel_alerta": self.ids["id_nivel_alerta"],
            "id_estado_alerta": self.ids["id_estado"]
        }
        
        response = self.client.post("/sgir/v1/crud/alertas/", json=alerta_payload, headers=self.headers)
        self.assertEqual(response.status_code, 201, f"Error al generar alerta: {response.text}")
        data = response.json()
        self.assertIn("id_alerta", data)
        self.__class__.ids["id_alerta"] = data["id_alerta"]
        print(f"[INSERT SUCCESS] Alerta registrada con ID: {data['id_alerta']}")

if __name__ == "__main__":
    unittest.main()
