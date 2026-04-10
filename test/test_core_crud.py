import requests
import random

BASE_URL = "http://localhost:8000/users/"

def test_list_users():
    response = requests.get(BASE_URL)
    assert response.status_code == 200
    print(f"List Users: {len(response.json())} users found.")

def test_create_user():
    email = f"test_{random.randint(1, 1000)}@example.com"
    payload = {
        "email": email,
        "nombres": "Test",
        "apellidos": "User",
        "password": "testpassword123",
        "id_rol": 1,
        "id_estado_usuario": 1
    }
    response = requests.post(BASE_URL, json=payload)
    assert response.status_code == 201
    user_id = response.json()["id_usuario"]
    print(f"Created User: ID {user_id}")
    return user_id

def test_get_user(user_id):
    response = requests.get(f"{BASE_URL}{user_id}")
    assert response.status_code == 200
    print(f"Get User: {response.json()['email']}")

def test_update_user(user_id):
    payload = {
        "email": f"updated_{user_id}@example.com",
        "nombres": "Updated",
        "apellidos": "User",
        "password": "newpassword123"
    }
    response = requests.put(f"{BASE_URL}{user_id}", json=payload)
    assert response.status_code == 200
    print(f"Updated User: {response.json()['nombres']}")

def test_delete_user(user_id):
    response = requests.delete(f"{BASE_URL}{user_id}")
    assert response.status_code == 204
    print(f"Deleted User: ID {user_id}")

if __name__ == "__main__":
    test_list_users()
    uid = test_create_user()
    test_get_user(uid)
    test_update_user(uid)
    test_delete_user(uid)
