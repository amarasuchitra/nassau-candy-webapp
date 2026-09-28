"""API tests — run with:  python -m pytest -q"""
import pytest
from fastapi.testclient import TestClient

from backend.main import app


@pytest.fixture(scope="module")
def client():
    with TestClient(app) as c:
        yield c


def test_health(client):
    r = client.get("/api/health")
    assert r.status_code == 200
    body = r.json()
    assert body["status"] == "ok" and body["model_loaded"]
    assert body["options"] == 1060 and body["recommendations"] == 212


def test_frontend_served(client):
    r = client.get("/")
    assert r.status_code == 200
    assert "Where should we ship this product from?" in r.text
    assert r.headers["x-content-type-options"] == "nosniff"


def test_static_bundle_fallback_exists(client):
    assert client.get("/data/dashboard_bundle.json").status_code == 200


def test_meta(client):
    m = client.get("/api/meta").json()
    assert len(m["products"]) == 15
    assert m["regions"] == ["Atlantic", "Gulf", "Interior", "Pacific"]
    assert len(m["factories"]) == 5 and len(m["ship_modes"]) == 4
    milk = next(p for p in m["products"] if p["name"] == "Wonka Bar - Milk Chocolate")
    assert milk["current_factory"] == "Wicked Choccy's"


def test_bundle_shape(client):
    b = client.get("/api/bundle").json()
    for key in ("dashboard_data", "recommendations", "factory_summary", "region_summary",
                "model_results", "factory_region_summary"):
        assert key in b
    assert len(b["dashboard_data"]) == 1060


def test_simulate_recommends_faster_factory(client):
    r = client.get("/api/simulate", params={"product": "Wonka Bar - Milk Chocolate", "region": "Pacific",
                                            "ship_mode": "Same Day"}).json()
    assert r["current_factory"] == "Wicked Choccy's"
    assert r["recommended_factory"] == "Lot's O' Nuts"
    assert r["days_faster"] == pytest.approx(3.19, abs=0.01)
    assert [row["lead_time_days"] for row in r["ranking"]] == sorted(row["lead_time_days"] for row in r["ranking"])


def test_simulate_combo_without_history_uses_correct_current_factory(client):
    # pick a product/region pair with no order history
    m = client.get("/api/meta").json()
    b = client.get("/api/bundle").json()
    have = {(r["product"], r["region"]) for r in b["dashboard_data"]}
    missing = next((p["name"], g) for p in m["products"] for g in m["regions"] if (p["name"], g) not in have)
    r = client.get("/api/simulate", params={"product": missing[0], "region": missing[1]}).json()
    expected = next(p["current_factory"] for p in m["products"] if p["name"] == missing[0])
    assert r["current_factory"] == expected
    assert all(row["estimated"] for row in r["ranking"])


def test_simulate_unknown_product_404(client):
    r = client.get("/api/simulate", params={"product": "Nope", "region": "Pacific"})
    assert r.status_code == 404 and "Unknown product" in r.json()["detail"]


def test_predict_matches_dashboard_grid(client):
    """Live model predictions reproduce the dashboard's numbers exactly."""
    b = client.get("/api/bundle").json()
    for row in b["dashboard_data"][::97]:
        p = client.post("/api/predict", json={"product": row["product"], "region": row["region"],
                                              "factory": row["factory"], "ship_mode": row["ship_mode"]}).json()
        assert p["distance_miles"] == row["distance"]
        assert p["predicted_lead_time_days"] == pytest.approx(row["lead_time"], abs=0.005)
        assert p["est_shipping_cost"] == pytest.approx(row["ship_cost"], abs=0.002)
        assert p["model"] == "Linear Regression"


def test_predict_validation(client):
    assert client.post("/api/predict", json={"product": "Nerds"}).status_code == 422
    assert client.post("/api/predict", json={"product": "Nerds", "region": "Gulf", "factory": "Secret Factory",
                                             "units": -1}).status_code == 422
    assert client.post("/api/predict", json={"product": "Nerds", "region": "Mars",
                                             "factory": "Secret Factory"}).status_code == 404


def test_compare(client):
    c = client.get("/api/compare", params={"product": "Nerds", "candidate": "Wicked Choccy's"}).json()
    assert c["current_factory"] == "Sugar Shack"
    assert c["lead_time_change_days"] == pytest.approx(-0.58, abs=0.01)
    assert c["candidate_is_faster"] is True
    assert c["orders_affected"] == 4


def test_recommendations_filters(client):
    all_ = client.get("/api/recommendations", params={"limit": 500}).json()
    assert all_["total"] == 212
    pac = client.get("/api/recommendations", params={"region": "Pacific", "min_orders": 100}).json()
    assert pac["total"] > 0
    assert all(r["Region"] == "Pacific" and r["orders_affected"] >= 100 for r in pac["items"])
    speed = client.get("/api/recommendations", params={"priority": 1}).json()["items"]
    assert speed[0]["lead_time_reduction_pct"] >= speed[-1]["lead_time_reduction_pct"]


def test_top_opportunities(client):
    top = client.get("/api/recommendations/top").json()
    assert len(top) == 3
    assert top[0]["product"] == "Wonka Bar - Milk Chocolate" and top[0]["move_to"] == "Lot's O' Nuts"
    assert top[0]["days_faster"] == pytest.approx(3.2, abs=0.05)


def test_risk_counts(client):
    r = client.get("/api/risk").json()
    assert r["profit_tradeoffs"]["count"] == 1
    assert r["low_confidence"]["count"] == 80


def test_summary(client):
    s = client.get("/api/summary").json()
    assert s["orders_analyzed"] > 10000
    assert s["win_win_routes"] > 0


def test_admin_rebuild_disabled_without_token(client):
    assert client.post("/api/admin/rebuild").status_code == 403


def test_unknown_api_route(client):
    assert client.get("/api/does-not-exist").status_code == 404
