"""Score appointments with the trained no-show model (ml/artifacts/model.pkl).

If the model can't be loaded (file missing, scikit-learn version mismatch), we
fall back to a simple rule so the demo still runs, and say so in the API
response (`risk_source`).
"""
from __future__ import annotations

import logging
import sys
from functools import lru_cache
from typing import TYPE_CHECKING

import pandas as pd

from app.core.config import settings

if TYPE_CHECKING:
    from app.models.db_models import Appointment

log = logging.getLogger(__name__)

# Reuse the exact feature code used in training (single source of truth).
if str(settings.ml_src) not in sys.path:
    sys.path.insert(0, str(settings.ml_src))
from features import build_features  # noqa: E402

FALLBACK_THRESHOLD = 0.35


@lru_cache(maxsize=1)
def load_model() -> dict | None:
    try:
        import joblib

        bundle = joblib.load(settings.model_path)
        log.info("Loaded %s from %s", bundle.get("model_name"), settings.model_path)
        return bundle
    except Exception as exc:  # noqa: BLE001
        log.warning("Could not load model (%s). Using fallback rule. Run `python ml/src/train.py`.", exc)
        return None


def risk_source() -> str:
    bundle = load_model()
    return bundle["model_name"] if bundle else "fallback_rule"


def high_risk_threshold() -> float:
    bundle = load_model()
    return float(bundle["high_risk_threshold"]) if bundle else FALLBACK_THRESHOLD


def _frame(appts: list["Appointment"]) -> pd.DataFrame:
    return pd.DataFrame(
        {
            "appt_date": [pd.Timestamp(a.start_time).normalize() for a in appts],
            "booked_at": [pd.Timestamp(a.booked_at) for a in appts],
            "age_raw": [a.age for a in appts],
            "Gender": [a.gender for a in appts],
            "scholarship": [a.scholarship for a in appts],
            "hypertension": [a.hypertension for a in appts],
            "diabetes": [a.diabetes for a in appts],
            "alcoholism": [a.alcoholism for a in appts],
            "handcap": [a.handcap for a in appts],
            "sms_received": [a.sms_received for a in appts],
            "prior_appts": [a.prior_appts for a in appts],
            "prior_noshows": [a.prior_noshows for a in appts],
        }
    )


def _fallback(features: pd.DataFrame) -> list[float]:
    """Rough rule from the notebook's findings: lead time and history matter most."""
    p = 0.05 + 0.25 * (features["lead_days"].clip(upper=30) / 30) + 0.4 * (features["prior_noshow_rate"] - 0.2)
    p = p - 0.1 * (features["age"] > 60)
    return [float(min(0.95, max(0.01, v))) for v in p]


def score(appts: list["Appointment"]) -> list[float]:
    if not appts:
        return []
    features = build_features(_frame(appts))
    bundle = load_model()
    if bundle is None:
        return _fallback(features)
    return [float(v) for v in bundle["pipeline"].predict_proba(features[bundle["features"]])[:, 1]]
