import requests

BASE_URL = "http://localhost:8000/mysql5"

def test_monitoring_metrics():
    # ID de instancia 2 es mysql5_db según la seed
    id_instancia = 2
    response = requests.get(f"{BASE_URL}/metrics/{id_instancia}")
    # Nota: Este test fallará si no hay sesión dinámica configurada o si falta autenticación
    print(f"Monitoring Status Code: {response.status_code}")
    if response.status_code == 200:
        print(f"Metrics: {response.json()}")
    else:
        print(f"Error: {response.text}")

if __name__ == "__main__":
    test_monitoring_metrics()
