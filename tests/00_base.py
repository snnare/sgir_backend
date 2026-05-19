import unittest
import httpx

class TestBaseRegister(unittest.TestCase):
    def setUp(self):
        # Apuntamos directamente al contenedor Docker en ejecución en el puerto 8000
        self.client = httpx.Client(base_url="http://localhost:8000")

    def tearDown(self):
        self.client.close()

    def test_register_admin(self):
        """Registra al usuario administrador base si no existe en el sistema golpeando el contenedor de Docker."""
        admin_data = {
            "email": "admin@admin.com",
            "nombres": "Administrador",
            "apellidos": "Sistema",
            "password": "123Nokia",
            "id_rol": 1,
            "id_estado_usuario": 1
        }
        
        # Enviar petición HTTP real por red al puerto 8000
        response = self.client.post("/sgir/v1/crud/users/", json=admin_data)
        
        # Si el usuario ya está registrado, el servidor retorna 400. Ambas respuestas son válidas.
        self.assertIn(response.status_code, [201, 400])
        if response.status_code == 201:
            print("\n[Base Test] Usuario admin@admin.com creado exitosamente en el contenedor.")
        else:
            print("\n[Base Test] Usuario admin@admin.com ya se encuentra registrado en el contenedor.")

if __name__ == "__main__":
    unittest.main()
