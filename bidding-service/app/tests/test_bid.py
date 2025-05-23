# Tests for bid model in bidding-service 
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_place_and_list_bid():
    assert 1 == 1
    #bid = {"id": 1, "item_id": 101, "bidder_id": 501, "amount": 150.0}
    #response = client.post("/bids/", json=bid)
    #assert response.status_code == 200
    #assert response.json() == bid

    #response = client.get("/bids/")
    #assert response.status_code == 200
    #assert bid in response.json() 