"""Emergency Mode endpoint: nearest ER, no insurance filter (EMTALA, decision #14)."""


def test_nearest_er_boston(client):
    res = client.get("/api/emergency/nearest-er?lat=42.30&lon=-71.07")
    assert res.status_code == 200
    body = res.json()

    nearest = body["nearest"]
    for key in ("name", "municipality", "county", "lat", "lon", "distance_miles"):
        assert key in nearest
    assert isinstance(nearest["distance_miles"], float)
    assert nearest["distance_miles"] >= 0

    top3 = body["top3"]
    assert len(top3) <= 3
    distances = [er["distance_miles"] for er in top3]
    assert distances == sorted(distances)


def test_far_away_query_has_different_nearest(client):
    boston = client.get("/api/emergency/nearest-er?lat=42.30&lon=-71.07").json()
    western = client.get("/api/emergency/nearest-er?lat=42.10&lon=-73.20").json()
    assert boston["nearest"]["name"] != western["nearest"]["name"]


def test_insurance_param_is_ignored(client):
    plain = client.get("/api/emergency/nearest-er?lat=42.30&lon=-71.07")
    with_insurance = client.get(
        "/api/emergency/nearest-er?lat=42.30&lon=-71.07&insurance=NO_INSURANCE"
    )
    assert with_insurance.status_code == 200
    assert with_insurance.json() == plain.json()
