"""Who should get offered a freed-up slot, and in what order."""
from __future__ import annotations

import math
from dataclasses import dataclass

from app.models.db_models import Clinic, Patient

EARTH_RADIUS_MILES = 3958.8


def haversine_miles(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
    """Great-circle distance. Same result PostGIS ST_Distance(geography) gives, to ~0.5%."""
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp, dl = p2 - p1, math.radians(lng2 - lng1)
    a = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * EARTH_RADIUS_MILES * math.asin(math.sqrt(a))


@dataclass
class Match:
    patient: Patient
    distance_miles: float
    score: float


def eligibility(patient: Patient, clinic: Clinic, radius_multiplier: float = 1.0) -> tuple[bool, str, float]:
    """(eligible, reason, distance). Reasons make the demo explainable."""
    distance = haversine_miles(patient.lat, patient.lng, clinic.lat, clinic.lng)
    if not patient.is_available:
        return False, "standby is off", distance
    if patient.specialty_needed != clinic.specialty:
        return False, "needs a different specialty", distance
    if not clinic.accepts(patient.insurance):
        return False, "insurance not accepted", distance
    if distance > patient.radius_miles * radius_multiplier:
        return False, "outside travel radius", distance
    return True, "eligible", distance


def rank_candidates(
    patients: list[Patient], clinic: Clinic, radius_multiplier: float = 1.0, exclude_ids: set[int] | None = None
) -> list[Match]:
    """Eligible patients, best first.

    Score = 60% reliability (do they show up for last-minute slots?)
          + 40% closeness (can they get there in time?).
    """
    exclude_ids = exclude_ids or set()
    matches = []
    for p in patients:
        if p.id in exclude_ids:
            continue
        ok, _, distance = eligibility(p, clinic, radius_multiplier)
        if not ok:
            continue
        max_dist = max(p.radius_miles * radius_multiplier, 0.1)
        closeness = 1 - min(distance / max_dist, 1)
        matches.append(Match(p, distance, 0.6 * p.reliability + 0.4 * closeness))
    return sorted(matches, key=lambda m: (-m.score, m.distance_miles, m.patient.id))
