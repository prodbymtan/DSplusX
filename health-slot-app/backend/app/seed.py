"""Load the demo: one clinic, today's schedule (scored by the model), standby patients.

Data comes from app/seed_data/demo_seed.json, built by ml/src/massachusetts.py from:
  - Synthea synthetic patients (Massachusetts): names, ages, sex, home locations,
    insurance, conditions, visit history. Not real people.
  - MassGIS / MA Department of Public Health licensed hospitals: real locations.

    python -m app.seed      # reset the database to the demo state
"""
from __future__ import annotations

import json
from datetime import datetime, timedelta
from pathlib import Path

from app.core.database import SessionLocal, reset_db
from app.models.db_models import Appointment, Clinic, Patient
from app.services import risk

SEED_FILE = Path(__file__).resolve().parent / "seed_data" / "demo_seed.json"


def load_seed_file() -> dict:
    return json.loads(SEED_FILE.read_text())


def seed(reset: bool = True) -> dict:
    data = load_seed_file()
    if reset:
        reset_db()
    today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)

    with SessionLocal() as db:
        c = data["clinic"]
        clinic = Clinic(
            name=c["name"],
            lat=c["lat"],
            lng=c["lng"],
            specialty=c["specialty"],
            accepted_insurance=",".join(c["accepted_insurance"]),
        )
        db.add(clinic)
        db.flush()

        for p in data["standby"]:
            db.add(
                Patient(
                    name=p["name"],
                    lat=p["lat"],
                    lng=p["lng"],
                    radius_miles=p["radius_miles"],
                    insurance=p["insurance"],
                    specialty_needed=p.get("specialty_needed", c["specialty"]),
                    reliability=p["reliability"],
                    is_available=True,
                )
            )

        appts = []
        for a in data["schedule"]:
            hh, mm = (int(x) for x in a["start"].split(":"))
            start = today + timedelta(hours=hh, minutes=mm)
            booked = today - timedelta(days=a["lead_days"]) + timedelta(hours=a["booked_hour"])
            appt = Appointment(
                clinic_id=clinic.id,
                patient_label=a["label"],
                start_time=start,
                duration_min=a.get("duration_min", 30),
                booked_at=booked,
                age=a["age"],
                gender=a["gender"],
                scholarship=a.get("scholarship", 0),
                hypertension=a.get("hypertension", 0),
                diabetes=a.get("diabetes", 0),
                alcoholism=a.get("alcoholism", 0),
                handcap=a.get("handcap", 0),
                sms_received=a.get("sms_received", 0),
                prior_appts=a.get("prior_appts", 0),
                prior_noshows=a.get("prior_noshows", 0),
                status="scheduled",
            )
            db.add(appt)
            appts.append(appt)

        for appt, p in zip(appts, risk.score(appts)):
            appt.risk = p
        db.commit()
        threshold = risk.high_risk_threshold()
        return {
            "clinic": clinic.name,
            "appointments": len(appts),
            "high_risk": sum(a.risk >= threshold for a in appts),
            "standby_patients": len(data["standby"]),
            "risk_source": risk.risk_source(),
        }


if __name__ == "__main__":
    print(seed(True))
