import requests

BASE_URL = "http://localhost:5000"

def test_health_check():
    response = requests.get(f"{BASE_URL}/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"

def test_create_visit():
    response = requests.post(f"{BASE_URL}/visits", json={"note": "ci test"})
    assert response.status_code == 201
