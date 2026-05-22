import unittest
import httpx
import time
import json

class TestBulkServersMonitoring(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.base_url = "http://localhost:8000"
        cls.client = httpx.Client(base_url=cls.base_url, timeout=30.0)
        cls.token = None
        cls.headers = {}

    @classmethod
    def tearDownClass(cls):
        cls.client.close()

    def test_01_login_admin(self):
        """1. Autenticación: Iniciar sesión con las credenciales provistas para el Administrador."""
        login_payload = {
            "username": "admin@admin.com",
            "password": "123Nokia"
        }
        response = self.client.post("/sgir/v1/crud/users/login", data=login_payload)
        self.assertEqual(response.status_code, 200, "Error en la autenticación del administrador. Verifica que el backend esté arriba y con la base de datos inicializada.")
        
        token_data = response.json()
        self.assertIn("access_token", token_data)
        self.__class__.token = token_data["access_token"]
        self.__class__.headers = {"Authorization": f"Bearer {self.token}"}
        print(f"\n🔑 [BULK TEST] Sesión iniciada con éxito para admin@admin.com.")

    def test_02_get_all_servers(self):
        """2. Obtener Servidores: Recupera el listado completo de servidores de la CMDB."""
        self.assertIsNotNone(self.token)
        
        start_time = time.time()
        response = self.client.get("/sgir/v1/crud/servidores/", headers=self.headers)
        elapsed = time.time() - start_time
        
        self.assertEqual(response.status_code, 200, f"Error al recuperar servidores: {response.text}")
        servers_list = response.json()
        self.assertIsInstance(servers_list, list, "El listado de servidores debe ser un JSON Array.")
        
        print(f"\n🖥️ [BULK TEST] Servidores registrados en CMDB: {len(servers_list)}")
        print(f"    Tiempo de respuesta: {elapsed:.3f}s")
        for srv in servers_list:
            print(f"    - ID: {srv.get('id_servidor')} | Nombre: {srv.get('nombre_servidor')} | IP: {srv.get('direccion_ip')} | Criticidad ID: {srv.get('id_nivel_criticidad')}")

    def test_03_get_host_global_summary(self):
        """3. Resumen Global de Salud: Recupera el consolidado de salud de hardware del Módulo 1."""
        self.assertIsNotNone(self.token)
        
        start_time = time.time()
        response = self.client.get("/sgir/v1/m1/host/global-summary", headers=self.headers)
        elapsed = time.time() - start_time
        
        self.assertEqual(response.status_code, 200, f"Error al recuperar resumen global: {response.text}")
        summary = response.json()
        
        self.assertIn("healthy", summary)
        self.assertIn("critical", summary)
        self.assertIn("stale", summary)
        self.assertIn("unknown", summary)
        self.assertIn("total_active_servers", summary)
        
        print(f"\n📊 [BULK TEST] Resumen Global de Salud (M1 Host):")
        print(f"    Total Activos: {summary['total_active_servers']} | Sanos (Healthy): {summary['healthy']} | Críticos (Critical): {summary['critical']} | Obsoletos/Desactualizados (Stale): {summary['stale']} | Desconocidos (Unknown): {summary['unknown']}")
        print(f"    Tiempo de respuesta: {elapsed:.3f}s")

    def test_04_get_host_live_cache(self):
        """4. Caché de Hosts en Tiempo Real: Recupera y valida el live-cache serializado del hardware."""
        self.assertIsNotNone(self.token)
        
        start_time = time.time()
        response = self.client.get("/sgir/v1/m1/host/live-cache", headers=self.headers)
        elapsed = time.time() - start_time
        
        self.assertEqual(response.status_code, 200, f"Error al recuperar host live-cache: {response.text}")
        cache_data = response.json()
        self.assertIsInstance(cache_data, dict, "El host live-cache debe ser un JSON Object indexado por IP.")
        
        print(f"\n⚡ [BULK TEST] Caché de Métricas de Host en RAM (Live Cache):")
        print(f"    Servidores en caché: {len(cache_data)}")
        print(f"    Tiempo de respuesta: {elapsed:.3f}s")
        for ip, metrics in cache_data.items():
            print(f"    - IP: {ip} -> {metrics}")

    def test_05_get_db_live_cache(self):
        """5. Caché de Bases de Datos en Tiempo Real: Recupera y valida el live-cache estructurado/piped de las DBs."""
        self.assertIsNotNone(self.token)
        
        start_time = time.time()
        response = self.client.get("/sgir/v1/m1/db/live-cache", headers=self.headers)
        elapsed = time.time() - start_time
        
        self.assertEqual(response.status_code, 200, f"Error al recuperar db live-cache: {response.text}")
        cache_data = response.json()
        self.assertIsInstance(cache_data, dict, "El db live-cache debe ser un JSON Object indexado por ID de instancia.")
        
        print(f"\n🛢️ [BULK TEST] Caché de Métricas de Base de Datos en RAM (Live Cache):")
        print(f"    Instancias en caché: {len(cache_data)}")
        print(f"    Tiempo de respuesta: {elapsed:.3f}s")
        for inst_id, val in cache_data.items():
            print(f"    - Instancia ID {inst_id} -> {val}")

    def test_06_get_global_inventory_assets(self):
        """6. Inventario Consolidado CMDB (M2): Recupera el inventario enriquecido agrupado por servidor/instancia."""
        self.assertIsNotNone(self.token)
        
        start_time = time.time()
        response = self.client.get("/sgir/v1/m2/inventory/assets", headers=self.headers)
        elapsed = time.time() - start_time
        
        self.assertEqual(response.status_code, 200, f"Error al recuperar inventario de activos: {response.text}")
        assets = response.json()
        self.assertIsInstance(assets, list, "El listado de activos globales debe ser una lista.")
        
        print(f"\n📂 [BULK TEST] Inventario Consolidado de Activos CMDB (LEFT JOIN Masivo):")
        print(f"    Activos registrados: {len(assets)}")
        print(f"    Tiempo de respuesta: {elapsed:.3f}s")
        for asset in assets:
            dbs = [db.get("nombre") for db in asset.get("bases_de_datos", [])]
            print(f"    - Servidor: {asset.get('servidor')} ({asset.get('ip')}) | Instancia: {asset.get('instancia')} ({asset.get('motor')}) | BDs: {dbs}")

    def test_07_bulk_parallel_discovery(self):
        """7. Descubrimiento Masivo Paralelo (M2): Ejecuta y mide la sincronización en paralelo de todas las instancias."""
        self.assertIsNotNone(self.token)
        
        print("\n🚀 [BULK TEST] Iniciando Auto-descubrimiento en paralelo para todas las instancias de base de datos activas...")
        start_time = time.time()
        response = self.client.post("/sgir/v1/m2/inventory/discover-all", headers=self.headers)
        elapsed = time.time() - start_time
        
        self.assertEqual(response.status_code, 200, f"Error en sincronización en paralelo: {response.text}")
        discovery_result = response.json()
        
        self.assertIn("total_instancias_encontradas", discovery_result)
        self.assertIn("instancias_procesadas_exitosamente", discovery_result)
        self.assertIn("total_db_size_mb", discovery_result)
        
        print(f"    Sincronización masiva finalizada con éxito.")
        print(f"    Instancias encontradas: {discovery_result['total_instancias_encontradas']}")
        print(f"    Instancias procesadas exitosamente: {discovery_result['instancias_procesadas_exitosamente']}")
        print(f"    Instancias fallidas: {discovery_result['instancias_fallidas']}")
        print(f"    Omitidas sin credencial: {discovery_result['omitidas_sin_credenciales']}")
        print(f"    Tamaño total de bases de datos: {discovery_result['total_db_size_mb']} MB")
        print(f"    Tiempo de ejecución en paralelo: {elapsed:.3f}s")

if __name__ == "__main__":
    unittest.main()
