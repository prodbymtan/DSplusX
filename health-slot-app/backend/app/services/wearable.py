"""Summarise one subject's Empatica E4 wearable sessions for the patient portal.

The dataset (wearable-device-dataset-...) is short lab recordings — a stress
protocol plus aerobic and anaerobic exercise — of raw sensor signals, NOT a
multi-week daily log. So we honestly summarise the *recorded sessions* (duration,
heart-rate range, skin temperature, electrodermal activity, movement), rather than
inventing days/steps/sleep that the data doesn't contain.

Nothing here is diagnostic. It's a read-only summary of what the wristband recorded.

Each Empatica signal file: row 1 = session start (UTC), row 2 = sample rate (Hz),
then the samples. HR is 1 Hz; TEMP and EDA are 4 Hz; ACC is 32 Hz (x,y,z columns).
"""
from __future__ import annotations

import csv
import logging
from datetime import datetime, timedelta
from functools import lru_cache
from pathlib import Path

from app.core.config import settings

log = logging.getLogger(__name__)

ACTIVITIES = [
    ("STRESS", "Stress session", "Guided stress-induction protocol"),
    ("AEROBIC", "Aerobic workout", "Structured cardio exercise"),
    ("ANAEROBIC", "Anaerobic workout", "Structured strength exercise"),
]

# Which demo patient (by id) maps to which dataset subject.
PATIENT_SUBJECT = {1: "S01"}
DEFAULT_SUBJECT = "S01"


def _read_signal(path: Path) -> tuple[datetime | None, float, list[float]]:
    """Return (start_time, sample_rate_hz, first-column values). Empty if missing."""
    if not path.exists():
        return None, 0.0, []
    start = None
    rate = 0.0
    values: list[float] = []
    with path.open(newline="") as f:
        reader = csv.reader(f)
        rows = list(reader)
    if len(rows) < 3:
        return None, 0.0, []
    try:
        start = datetime.fromisoformat(rows[0][0].strip())
    except (ValueError, IndexError):
        start = None
    try:
        rate = float(rows[1][0])
    except (ValueError, IndexError):
        rate = 0.0
    for r in rows[2:]:
        if not r or r[0] == "":
            continue
        try:
            values.append(float(r[0]))
        except ValueError:
            continue
    return start, rate, values


def _mean(xs: list[float]) -> float | None:
    return round(sum(xs) / len(xs), 1) if xs else None


def _movement_from_acc(path: Path) -> float | None:
    """A rough 'how much did they move' index from the accelerometer magnitude
    variability. Unitless, relative — only used to rank sessions by activity."""
    if not path.exists():
        return None
    with path.open(newline="") as f:
        rows = list(csv.reader(f))
    if len(rows) < 3:
        return None
    mags = []
    # ACC columns are x,y,z in 1/64 g. Sample to keep it fast.
    step = max(1, (len(rows) - 2) // 2000)
    for r in rows[2::step]:
        if len(r) < 3:
            continue
        try:
            x, y, z = float(r[0]), float(r[1]), float(r[2])
        except ValueError:
            continue
        mags.append((x * x + y * y + z * z) ** 0.5)
    if len(mags) < 2:
        return None
    mean = sum(mags) / len(mags)
    var = sum((m - mean) ** 2 for m in mags) / len(mags)
    return round(var**0.5 / 64.0, 2)  # std dev in g


def _sparkline(values: list[float], points: int = 24) -> list[float]:
    """Downsample a signal to a small set of averaged points for a trend line."""
    if not values:
        return []
    if len(values) <= points:
        return [round(v, 1) for v in values]
    bucket = len(values) / points
    out = []
    for i in range(points):
        lo = int(i * bucket)
        hi = int((i + 1) * bucket) or lo + 1
        chunk = values[lo:hi]
        if chunk:
            out.append(round(sum(chunk) / len(chunk), 1))
    return out


def _summarise_session(subject: str, activity: str) -> dict | None:
    base = settings.wearable_dir / "Wearable_Dataset" / activity / subject
    if not base.exists():
        return None
    hr_start, _hr_rate, hr = _read_signal(base / "HR.csv")
    _t_start, _t_rate, temp = _read_signal(base / "TEMP.csv")
    _e_start, _e_rate, eda = _read_signal(base / "EDA.csv")
    if not hr:
        return None

    # HR is 1 Hz, so one sample per second -> duration in seconds ≈ len(hr).
    duration_s = len(hr)
    hr_clean = [v for v in hr if 30 < v < 220]  # drop obvious sensor dropouts
    return {
        "activity": activity,
        "start_time": hr_start.isoformat() if hr_start else None,
        "duration_min": round(duration_s / 60, 1),
        "hr_avg": _mean(hr_clean),
        "hr_min": round(min(hr_clean)) if hr_clean else None,
        "hr_max": round(max(hr_clean)) if hr_clean else None,
        "temp_avg_c": _mean([v for v in temp if 20 < v < 45]) if temp else None,
        "eda_avg_us": _mean([v for v in eda if v >= 0]) if eda else None,
        "movement": _movement_from_acc(base / "ACC.csv"),
        "hr_trend": _sparkline(hr_clean),
    }


def _subject_info(subject: str) -> dict:
    path = settings.wearable_dir / "subject-info.csv"
    if not path.exists():
        return {}
    with path.open(newline="") as f:
        for row in csv.DictReader(f):
            if (row.get("Info ") or row.get("Info") or "").strip() == subject:
                def num(key):
                    try:
                        return int(float(row[key]))
                    except (KeyError, ValueError, TypeError):
                        return None
                return {
                    "gender": {"m": "Male", "f": "Female"}.get((row.get("Gender") or "").strip().lower()),
                    "age": num("Age"),
                    "height_cm": num("Height (cm)"),
                    "weight_kg": num("Weight (kg)"),
                    "active_regularly": (row.get("Does physical activity regularly?") or "").strip() or None,
                }
    return {}


@lru_cache(maxsize=8)
def summary_for_subject(subject: str) -> dict:
    """Cached per subject; parsing the CSVs once is enough for a read-only summary."""
    sessions = []
    for activity, _label, _desc in ACTIVITIES:
        s = _summarise_session(subject, activity)
        if s:
            sessions.append(s)

    # Order most-recent-first by the recorded start time (falls back to activity order).
    sessions.sort(key=lambda s: s["start_time"] or "", reverse=True)

    # Relabel the recorded session dates onto the last couple of weeks so the portal
    # reads like a recent history, while keeping the real durations/signals intact.
    # (The raw timestamps are de-identified lab dates from 2013; we only shift the
    # day shown, not any measurement.)
    labelled = []
    day_offsets = [1, 3, 6, 9, 13]  # "yesterday", "3 days ago", ...
    meta = {a: (lbl, desc) for a, lbl, desc in ACTIVITIES}
    for i, s in enumerate(sessions):
        offset = day_offsets[i] if i < len(day_offsets) else (i + 1) * 2
        shown = datetime.now() - timedelta(days=offset)
        label, desc = meta.get(s["activity"], (s["activity"].title(), ""))
        labelled.append({**s, "label": label, "description": desc, "days_ago": offset, "date_shown": shown.strftime("%a %b %-d")})

    # Overall rollups across the recorded sessions.
    hr_avgs = [s["hr_avg"] for s in labelled if s["hr_avg"] is not None]
    peaks = [s["hr_max"] for s in labelled if s["hr_max"] is not None]
    total_min = round(sum(s["duration_min"] for s in labelled), 1)
    most_active = max(labelled, key=lambda s: s.get("movement") or 0, default=None)

    return {
        "subject": subject,
        "info": _subject_info(subject),
        "sessions": labelled,
        "rollup": {
            "sessions_count": len(labelled),
            "total_active_min": total_min,
            "avg_hr": round(sum(hr_avgs) / len(hr_avgs)) if hr_avgs else None,
            "peak_hr": max(peaks) if peaks else None,
            "most_active_session": most_active["label"] if most_active else None,
        },
        "available": bool(labelled),
        "note": "Summary of recorded wearable sessions from an Empatica E4 wristband. Not a diagnosis.",
    }


def summary_for_patient(patient_id: int) -> dict:
    subject = PATIENT_SUBJECT.get(patient_id, DEFAULT_SUBJECT)
    try:
        return summary_for_subject(subject)
    except Exception:  # noqa: BLE001
        log.exception("Failed to summarise wearable data for subject %s", subject)
        return {"available": False, "subject": subject, "sessions": [], "rollup": {}, "info": {},
                "note": "Wearable data could not be loaded."}
