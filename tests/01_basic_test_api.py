import unittest
from fastapi.testclient import TestClient
from app.main import app

class TestHealthEndpoints(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)

    def test_root_endpoint(self):
        """Valida el endpoint raíz '/' del backend."""
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"message": "Welcome"})

    def test_ping_endpoint(self):
        """Valida el endpoint de ping básico '/ping'."""
        response = self.client.get("/ping")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"status": "ok", "message": "Backend is reachable"})

    def test_health_postgres(self):
        """Valida el endpoint de estado de PostgreSQL con el nuevo prefijo '/sgir/v1/health/postgres'."""
        response = self.client.get("/sgir/v1/health/postgres")
        # Si la base de datos no está disponible en este entorno, podría devolver 500
        if response.status_code == 200:
            data = response.json()
            self.assertEqual(data["status"], "ok")
            self.assertEqual(data["db"], "PostgreSQL")
            self.assertIn("result", data)
        else:
            self.assertEqual(response.status_code, 500)
            self.assertIn("detail", response.json())

    def test_health_ping(self):
        """Valida el endpoint de ping remoto con el nuevo prefijo '/sgir/v1/health/ping'."""
        payload = {"ip": "127.0.0.1"}
        response = self.client.post("/sgir/v1/health/ping", json=payload)
        self.assertEqual(response.status_code, 200)
        self.assertIsInstance(response.json(), bool)

if __name__ == "__main__":
    unittest.main()
