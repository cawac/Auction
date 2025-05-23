from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_register_user():
    response = client.post("/register", json={
        "first_name": "Alice",
        "last_name": "Smith",
        "email": "alice@example.com",
        "password": "securepass",
        "phone_number": "+37012345678"
    })
    assert response.status_code == 200
    assert response.json()["email"] == "alice@example.com"
