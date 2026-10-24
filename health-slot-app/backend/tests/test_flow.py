"""End-to-end tests of the release -> offer -> ripple -> claim workflow.

    cd backend && pytest -q
"""
import threading
import time

from app.core.database import SessionLocal
from app.models.db_models import Patient
from app.services import offers
from app.services.offers import ServiceError


def patients_by_name(client):
    return {p["name"]: p for p in client.get("/api/patients").json()}


def high_risk_appointment(client):
    appts = client.get("/api/appointments").json()["appointments"]
    return next(a for a in appts if a["high_risk"])


def test_schedule_is_scored_by_trained_model(client):
    body = client.get("/api/appointments").json()
    assert body["risk_source"] == "gradient_boosting"
    assert len(body["appointments"]) == 10
    assert any(a["high_risk"] for a in body["appointments"])
    assert all(0 < a["risk"] < 1 for a in body["appointments"])


def test_release_offers_only_eligible_patients(client):
    by_name = patients_by_name(client)
    eligible = {n for n, p in by_name.items() if p["eligible_now"]}
    assert eligible, "seed should have patients in range"
    assert any(p["eligibility_reason"] == "outside travel radius" for p in by_name.values())
    assert any(p["eligibility_reason"] == "insurance not accepted" for p in by_name.values())

    appt = high_risk_appointment(client)
    slot = client.post(f"/api/appointments/{appt['id']}/unconfirmed").json()
    assert slot["status"] == "open"
    assert {o["name"] for o in slot["offered"]} == eligible


def test_first_claim_wins_others_rejected(client):
    by_name = patients_by_name(client)
    eligible = [p for p in by_name.values() if p["eligible_now"]]
    outsider = next(p for p in by_name.values() if p["eligibility_reason"] == "insurance not accepted")
    appt = high_risk_appointment(client)
    slot = client.post(f"/api/appointments/{appt['id']}/no-show").json()

    first, second = eligible[0], eligible[1]
    r1 = client.post(f"/api/slots/{slot['id']}/claim", json={"patient_id": first["id"]})
    assert r1.status_code == 200 and r1.json()["status"] == "booked"
    r2 = client.post(f"/api/slots/{slot['id']}/claim", json={"patient_id": second["id"]})
    assert r2.status_code == 409
    r3 = client.post(f"/api/slots/{slot['id']}/claim", json={"patient_id": outsider["id"]})
    assert r3.status_code == 403

    state = client.get(f"/api/patients/{first['id']}/state").json()
    assert state["history"][0]["outcome"] == "booked"
    assert state["patient"]["is_available"] is False  # standby paused after booking
    loser = client.get(f"/api/patients/{second['id']}/state").json()
    assert loser["history"][0]["outcome"] == "taken"
    live = client.get("/api/metrics").json()["live"]
    assert live["slots_recovered"] == 1 and live["minutes_recovered"] == 30


def test_cannot_release_twice(client):
    appt = high_risk_appointment(client)
    assert client.post(f"/api/appointments/{appt['id']}/cancel").status_code == 200
    assert client.post(f"/api/appointments/{appt['id']}/cancel").status_code == 409
    assert client.post("/api/appointments/9999/cancel").status_code == 404


def test_ripple_widens_radius_then_expires(client):
    by_name = patients_by_name(client)
    far = next(p for p in by_name.values() if p["eligibility_reason"] == "outside travel radius")
    appt = high_risk_appointment(client)
    slot = client.post(f"/api/appointments/{appt['id']}/unconfirmed").json()
    assert far["id"] not in {o["patient_id"] for o in slot["offered"]}

    time.sleep(1.6)  # one offer window: radius doubles
    state = client.get(f"/api/patients/{far['id']}/state").json()
    assert [o["round"] for o in state["offers"]] == [1]

    time.sleep(1.4)  # final window passes: slot expires
    s = client.get("/api/slots").json()[0]
    assert s["status"] == "expired"
    assert client.post(f"/api/slots/{s['id']}/claim", json={"patient_id": far["id"]}).status_code == 409


def test_websocket_pushes_offer_to_phone(client):
    eligible = next(p for p in patients_by_name(client).values() if p["eligible_now"])
    with client.websocket_connect(f"/ws/patients/{eligible['id']}") as ws:
        assert ws.receive_json()["type"] == "hello"
        appt = high_risk_appointment(client)
        client.post(f"/api/appointments/{appt['id']}/no-show")
        msg = ws.receive_json()
        assert msg["type"] == "offer"
        assert msg["offer"]["time_label"] == appt["time_label"]


def test_concurrent_claims_exactly_one_winner(client):
    """20 patients tap Claim at the same instant. Exactly one gets the slot."""
    with SessionLocal() as db:
        clinic_lat, clinic_lng = 42.3489, -71.0951
        for i in range(20):
            db.add(
                Patient(
                    name=f"Racer {i}", lat=clinic_lat + 0.001 * (i % 5), lng=clinic_lng, radius_miles=5,
                    insurance="Medicaid", specialty_needed="primary_care", reliability=0.9, is_available=True,
                )
            )
        db.commit()
        racer_ids = [p.id for p in db.query(Patient).filter(Patient.name.like("Racer %"))]

    appt = high_risk_appointment(client)
    slot_id = offers._open_slot(appt["id"], "no_show")["slot"]["id"]

    barrier = threading.Barrier(len(racer_ids))
    results = []

    def attempt(pid):
        barrier.wait()
        try:
            offers._claim(slot_id, pid)
            results.append("won")
        except ServiceError as e:
            results.append(e.status_code)

    threads = [threading.Thread(target=attempt, args=(pid,)) for pid in racer_ids]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    assert results.count("won") == 1
    assert results.count(409) == len(racer_ids) - 1


def test_reset_restores_demo(client):
    appt = high_risk_appointment(client)
    client.post(f"/api/appointments/{appt['id']}/no-show")
    summary = client.post("/api/demo/reset").json()
    assert summary["appointments"] == 10
    assert all(a["status"] == "scheduled" for a in client.get("/api/appointments").json()["appointments"])
    assert client.get("/api/slots").json() == []


def test_map_has_real_hospitals(client):
    m = client.get("/api/map").json()
    assert len(m["hospitals"]) >= 5
    assert all(h["distance_miles"] < 10 for h in m["hospitals"])


def test_fallback_rule_when_model_missing():
    import pandas as pd

    from app.services import risk
    from features import build_features

    df = pd.DataFrame(
        {
            "appt_date": [pd.Timestamp("2026-10-24")] * 2, "booked_at": [pd.Timestamp("2026-10-24"), pd.Timestamp("2026-09-01")],
            "age_raw": [70, 25], "Gender": ["F", "M"], "scholarship": [0, 0], "hypertension": [0, 0], "diabetes": [0, 0],
            "alcoholism": [0, 0], "handcap": [0, 0], "sms_received": [0, 1], "prior_appts": [3, 3], "prior_noshows": [0, 2],
        }
    )
    low, high = risk._fallback(build_features(df))
    assert 0 < low < high < 1
