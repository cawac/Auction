from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

def test_create_and_list_transaction():
    pass
    transaction = {"id": 1, "item_id": 101, "buyer_id": 501, "amount": 250.0, "status": "completed"}
    response = client.post("/transactions/", json=transaction)
    assert response.status_code == 200
    assert response.json() == transaction

    response = client.get("/transactions/")
    assert response.status_code == 200
    assert transaction in response.json()
