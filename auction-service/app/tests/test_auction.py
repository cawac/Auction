from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_create_auction():
    response = client.post("/auctions", json={
        "item_id": 101,
        "start_time": "2024-01-01T00:00:00",
        "end_date": "2024-01-02T00:00:00",
        "starting_price": 100.0,
        "current_price": 100.0,
        "status": "Active"
    })
    assert response.status_code == 201
    assert response.json()["status"] == "Active" 