import unittest
import httpx

class TestPdfReportEndpoint(unittest.TestCase):
    def setUp(self):
        self.client = httpx.Client(base_url="http://localhost:8000")
        self.login_data = {
            "username": "admin@admin.com",
            "password": "123Nokia"
        }

    def tearDown(self):
        self.client.close()

    def test_pdf_generation_flow(self):
        """Prueba de inicio de sesión y consulta al endpoint del PDF."""
        # 1. Iniciar sesión con las credenciales indicadas
        print("\n[TEST] Intentando iniciar sesión en el backend...")
        login_response = self.client.post("/sgir/v1/crud/users/login", data=self.login_data)
        
        self.assertEqual(login_response.status_code, 200, f"Fallo al logear: {login_response.text}")
        token_data = login_response.json()
        self.assertIn("access_token", token_data)
        print("[TEST] Inicio de sesión exitoso. Token obtenido.")
        
        headers = {"Authorization": f"Bearer {token_data['access_token']}"}

        # 2. Consultar el endpoint de generación de PDF
        print("[TEST] Consultando el endpoint GET /sgir/v1/assets/pdf ...")
        response = self.client.get("/sgir/v1/assets/pdf", headers=headers)
        
        print(f"[TEST] Código de Estado Recibido: {response.status_code}")
        
        if response.status_code == 500:
            print("\n[ERROR 500 DETECTADO] Detalle devuelto por el servidor:")
            try:
                error_json = response.json()
                print(f"Mensaje de error: {error_json.get('detail')}")
                print(f"Error detallado completo: {error_json}")
            except Exception:
                print(response.text)
        
        self.assertEqual(response.status_code, 200, f"Error en el endpoint: {response.text}")
        self.assertEqual(response.headers.get("content-type"), "application/pdf")
        print("[TEST] ¡Reporte PDF generado y descargado con éxito!")

if __name__ == "__main__":
    unittest.main()
