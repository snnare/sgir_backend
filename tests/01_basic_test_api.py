import unittest
import httpx

class TestSgirEndpoints(unittest.TestCase):
    def setUp(self):
        # Apuntamos directamente al contenedor Docker en ejecución en el puerto 8000
        self.client = httpx.Client(base_url="http://localhost:8000")
        self.admin_user_data = {
            "nombres": "AdminTest",
            "apellidos": "Sgir",
            "email": "testadmin@sgir.com",
            "password": "StrongPassword123",
            "id_rol": 1,
            "id_estado_usuario": 1
        }

    def tearDown(self):
        self.client.close()

    def test_root_endpoint(self):
        """Valida el endpoint raíz '/' del backend golpeando el contenedor de Docker."""
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"message": "Welcome"})

    def test_ping_endpoint(self):
        """Valida el endpoint de ping básico '/ping' golpeando el contenedor de Docker."""
        response = self.client.get("/ping")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"status": "ok", "message": "Backend is reachable"})

    def test_health_postgres(self):
        """Valida el endpoint de estado de PostgreSQL con el prefijo '/sgir/v1/m1/health/postgres' golpeando el contenedor."""
        response = self.client.get("/sgir/v1/m1/health/postgres")
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
        """Valida el endpoint de ping remoto con el prefijo '/sgir/v1/m1/health/ping' golpeando el contenedor."""
        payload = {"ip": "127.0.0.1"}
        response = self.client.post("/sgir/v1/m1/health/ping", json=payload)
        self.assertEqual(response.status_code, 200)
        # El endpoint debe retornar un booleano (True o False) indicando conectividad
        self.assertIsInstance(response.json(), bool)

    def test_crud_flow_authentication_and_list(self):
        """Valida el flujo CRUD: registro, inicio de sesión y obtención de recursos con el prefijo '/sgir/v1/crud/' golpeando el contenedor."""
        
        # 1. Registrar usuario de prueba (público) en /sgir/v1/crud/users/
        reg_response = self.client.post("/sgir/v1/crud/users/", json=self.admin_user_data)
        self.assertIn(reg_response.status_code, [201, 400])
        
        # 2. Iniciar sesión para obtener el Token OAuth2 en /sgir/v1/crud/users/login
        login_payload = {
            "username": self.admin_user_data["email"],
            "password": self.admin_user_data["password"]
        }
        # Formulario x-www-form-urlencoded
        login_response = self.client.post("/sgir/v1/crud/users/login", data=login_payload)
        self.assertEqual(login_response.status_code, 200)
        token_data = login_response.json()
        self.assertIn("access_token", token_data)
        self.assertEqual(token_data["token_type"], "bearer")
        
        # 3. Consumir un recurso CRUD protegido (Estados Generales) usando el Bearer Token en /sgir/v1/crud/estados/
        headers = {"Authorization": f"Bearer {token_data['access_token']}"}
        estados_response = self.client.get("/sgir/v1/crud/estados/", headers=headers)
        
        self.assertEqual(estados_response.status_code, 200)
        self.assertIsInstance(estados_response.json(), list)

if __name__ == "__main__":
    unittest.main()
