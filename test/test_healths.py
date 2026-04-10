import requests

def test_health_ping():
    response = requests.get("http://localhost:8000/health/ping?ip=127.0.0.1")
    assert response.status_code == 200
    print(f"Health Ping: {response.json()}")

def test_health_postgres():
    response = requests.get("http://localhost:8000/health/postgres")
    assert response.status_code == 200
    print(f"Health Postgres: {response.json()}")

if __name__ == "__main__":
    test_health_ping()
    test_health_postgres()
