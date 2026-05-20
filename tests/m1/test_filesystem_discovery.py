import unittest
import httpx
import json

class TestFilesystemDiscovery(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.base_url = "http://localhost:8000"
        cls.client = httpx.Client(base_url=cls.base_url)
        cls.token = None
        cls.headers = {}
        cls.id_servidor_test = 10 # ID solicitado por el usuario

    @classmethod
    def tearDownClass(cls):
        cls.client.close()

    def test_01_login(self):
        """1. Autenticación: Obtiene el token JWT para el administrador."""
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
        print("\n[TEST] Autenticación exitosa.")

    def test_02_verify_method_post(self):
        """2. Verificación de Método: Comprueba que el endpoint acepte POST y no GET."""
        self.assertIsNotNone(self.token)
        
        # Probar con POST (debería dar 400 si el server 10 no existe o no tiene SSH, pero NO 405)
        response_post = self.client.post(
            f"/sgir/v1/m1/host/discover-filesystems/{self.id_servidor_test}", 
            headers=self.headers,
            json={}
        )
        
        print(f"[TEST] POST Response Status: {response_post.status_code}")
        # Si el servidor no existe o no tiene credenciales, esperamos 400 (según implementación)
        # Lo importante es que no sea 405.
        self.assertNotEqual(response_post.status_code, 405, "El endpoint sigue rechazando el método POST.")
        
        # Probar con GET (debería dar 405 ahora)
        response_get = self.client.get(
            f"/sgir/v1/m1/host/discover-filesystems/{self.id_servidor_test}", 
            headers=self.headers
        )
        print(f"[TEST] GET Response Status: {response_get.status_code}")
        self.assertEqual(response_get.status_code, 405, "El endpoint debería rechazar el método GET ahora.")

    def test_03_discovery_execution_logic(self):
        """3. Lógica de Ejecución: Verifica que si el servidor existe, intente realizar el descubrimiento."""
        # Buscamos un servidor que tenga monitoreo_host activo para una prueba más real
        res = self.client.get("/sgir/v1/crud/servidores/", headers=self.headers)
        servidores = res.json()
        
        target_id = self.id_servidor_test
        for srv in servidores:
            if srv["monitoreo_host"]:
                target_id = srv["id_servidor"]
                break
        
        print(f"[TEST] Probando descubrimiento en Servidor ID: {target_id}")
        response = self.client.post(
            f"/sgir/v1/m1/host/discover-filesystems/{target_id}", 
            headers=self.headers,
            json={}
        )
        
        data = response.json()
        if response.status_code == 200:
            print("[TEST] Descubrimiento exitoso:")
            print(json.dumps(data, indent=2))
            self.assertIn("id_server", data)
            self.assertIn("ip_server", data)
            self.assertIn("filesystems", data)
            self.assertIsInstance(data["filesystems"], list)
        else:
            print(f"[TEST] Respuesta esperada de error/no-configurado: {data.get('detail', data)}")
            # Si falla por falta de credenciales (común en CI), el status debe ser 400
            self.assertIn(response.status_code, [200, 400])

if __name__ == "__main__":
    unittest.main()
