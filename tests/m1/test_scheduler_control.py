import unittest
import httpx

class TestSchedulerControl(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.base_url = "http://localhost:8000"
        cls.client = httpx.Client(base_url=cls.base_url)
        cls.token = None
        cls.headers = {}

    @classmethod
    def tearDownClass(cls):
        cls.client.close()

    def test_01_login(self):
        """1. Autenticación: Realiza login con la cuenta de administrador."""
        login_payload = {
            "username": "admin@admin.com",
            "password": "123Nokia"
        }
        response = self.client.post("/sgir/v1/crud/users/login", data=login_payload)
        self.assertEqual(response.status_code, 200, "Error en el login del administrador.")
        
        token_data = response.json()
        self.assertIn("access_token", token_data)
        self.__class__.token = token_data["access_token"]
        self.__class__.headers = {"Authorization": f"Bearer {self.token}"}
        print("\n[SCHEDULER TEST] Autenticación exitosa. Token obtenido.")

    def test_02_get_initial_status(self):
        """2. Estado Inicial: Consulta el estado inicial del scheduler."""
        self.assertIsNotNone(self.token)
        response = self.client.get("/sgir/v1/m1/host/scheduler/status", headers=self.headers)
        self.assertEqual(response.status_code, 200)
        
        status_data = response.json()
        self.assertIn("status", status_data)
        print(f"[SCHEDULER TEST] Estado inicial detectado: {status_data['status']}")

    def test_03_pause_scheduler(self):
        """3. Pausar: Solicita pausar la ejecución del scheduler."""
        self.assertIsNotNone(self.token)
        response = self.client.post("/sgir/v1/m1/host/scheduler/pause", headers=self.headers)
        self.assertEqual(response.status_code, 200)
        
        pause_data = response.json()
        print(f"[SCHEDULER TEST] Respuesta de pausa: {pause_data}")
        
        # Verificar estado tras pausar
        status_response = self.client.get("/sgir/v1/m1/host/scheduler/status", headers=self.headers)
        self.assertEqual(status_response.status_code, 200)
        self.assertEqual(status_response.json()["status"], "paused", "El scheduler debería estar pausado.")
        print("[SCHEDULER TEST] Confirmado: El scheduler se encuentra en estado 'paused'.")

    def test_04_resume_scheduler(self):
        """4. Reanudar: Solicita reactivar el scheduler de monitoreo."""
        self.assertIsNotNone(self.token)
        response = self.client.post("/sgir/v1/m1/host/scheduler/resume", headers=self.headers)
        self.assertEqual(response.status_code, 200)
        
        resume_data = response.json()
        print(f"[SCHEDULER TEST] Respuesta de reanudación: {resume_data}")
        
        # Verificar estado tras reanudar
        status_response = self.client.get("/sgir/v1/m1/host/scheduler/status", headers=self.headers)
        self.assertEqual(status_response.status_code, 200)
        self.assertEqual(status_response.json()["status"], "running", "El scheduler debería estar corriendo.")
        print("[SCHEDULER TEST] Confirmado: El scheduler se encuentra en estado 'running'.")

if __name__ == "__main__":
    unittest.main()
