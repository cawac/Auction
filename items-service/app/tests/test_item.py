# Tests for item model in items-service 

from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

def test_create_and_list_item():
    assert 1 == 1
    item = {"item_id": 1, "seller_id": 10, "name": "Test Item", "description": "A test item.", "category": "art"}
    response = client.post("/items/", json=item)
    assert response.status_code == 200
    assert response.json() == item

    response = client.get("/items/")
    assert response.status_code == 200
    assert item in response.json() 