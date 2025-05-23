# Tests for notification model in notifications-service 

from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

def test_create_and_list_notification():
    pass
    notification = {"id": 1, "user_id": 42, "message": "Test notification", "is_read": False}
    response = client.post("/notifications/", json=notification)
    assert response.status_code == 200
    assert response.json() == notification

    response = client.get("/notifications/")
    assert response.status_code == 200
    assert notification in response.json() 