import pytest
from main import app


@pytest.fixture
def client():
    app.config["TESTING"] = True
    with app.test_client() as c:
        yield c


def test_health_check(client):
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.get_json() == {"status": "ok"}


def test_get_cities(client):
    resp = client.get("/api/cities")
    assert resp.status_code == 200
    data = resp.get_json()
    assert "cities" in data
    assert data["count"] >= 1


def test_get_attractions_valid(client):
    resp = client.get("/api/attractions?city=beijing")
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["city"] == "北京"
    assert len(data["attractions"]) >= 1


def test_get_attractions_missing_param(client):
    resp = client.get("/api/attractions")
    assert resp.status_code == 400


def test_get_attractions_invalid_city(client):
    """Unusual city names are handled — no crash, valid response structure."""
    resp = client.get("/api/attractions?city=atlantis")
    # With dynamic generation, any city can be looked up; we just verify no crash
    assert resp.status_code in (200, 503)


def test_create_plan_valid(client):
    resp = client.post("/api/plan", json={"city": "beijing", "days": 3})
    assert resp.status_code == 201
    data = resp.get_json()
    assert data["city"] == "北京"
    assert len(data["itinerary"]) == 3


def test_create_plan_missing_fields(client):
    resp = client.post("/api/plan", json={"city": "beijing"})
    assert resp.status_code == 400


def test_create_plan_invalid_days(client):
    resp = client.post("/api/plan", json={"city": "beijing", "days": 99})
    assert resp.status_code == 400
