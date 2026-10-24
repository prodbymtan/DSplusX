"""Fill-rate simulation: how many no-show slots can we refill?

Today a no-show is discovered ~15 minutes after the slot starts, so it is
almost never refilled. Our system instead:

1. Each day, sends a "confirm you're coming" prompt to a budget of patients
   (default: 20% of the day's appointments).
2. Anyone who doesn't confirm by 30 minutes before has their slot released.
3. A released slot is offered to nearby standby patients; first to claim wins.

We compare two ways of choosing WHO gets a prompt, with the same budget:
  - random:  no model (what you'd do without data science)
  - model:   highest predicted no-show risk first

Everything is computed as an expected value (no random draws), so the numbers
are reproducible. The behavioural rates below are ASSUMPTIONS, not measured
from the dataset. Say so in the pitch, and show the budget curve so judges see
the trade-off instead of one cherry-picked number.
"""
from __future__ import annotations

import math

import numpy as np
import pandas as pd

DEFAULT_ASSUMPTIONS = {
    # Share of patients who WILL attend that answer the confirmation prompt.
    "confirm_rate_if_will_show": 0.80,
    # Share of eventual no-shows who still confirm (people say yes and then don't come).
    "confirm_rate_if_will_noshow": 0.10,
    # Average number of eligible standby patients within radius when a slot opens.
    "standby_patients_in_radius": 3.0,
    # Chance any one of them claims the slot in time.
    "standby_accept_prob": 0.35,
}


def fill_probability(a: dict) -> float:
    """P(at least one standby patient claims) with a Poisson number of nearby patients."""
    return 1 - math.exp(-a["standby_patients_in_radius"] * a["standby_accept_prob"])


def catch_rate(y: np.ndarray, p: np.ndarray, frac: float) -> float:
    """Share of all no-shows that land in the top `frac` of predicted risk."""
    y, p = np.asarray(y), np.asarray(p)
    k = max(1, int(round(frac * len(p))))
    top = np.argsort(-p, kind="stable")[:k]
    return float(y[top].sum() / max(1, y.sum()))


def _policy(day_df: pd.DataFrame, budget: float, how: str, a: dict) -> dict:
    """Expected outcome for one policy across all days."""
    f = fill_probability(a)
    release_ns = 1 - a["confirm_rate_if_will_noshow"]
    release_show = 1 - a["confirm_rate_if_will_show"]
    recovered = conflicts = prompts = 0.0

    for _, day in day_df.groupby("appt_date"):
        n = len(day)
        k = int(round(budget * n))
        if k == 0:
            continue
        prompts += k
        y = day["y"].to_numpy()
        if how == "model":
            chosen = np.argsort(-day["p"].to_numpy(), kind="stable")[:k]
            n_ns, n_show = y[chosen].sum(), k - y[chosen].sum()
        elif how == "random":
            # Expected composition of a random sample of size k.
            n_ns = k * y.mean()
            n_show = k - n_ns
        else:
            raise ValueError(how)
        recovered += n_ns * release_ns * f
        conflicts += n_show * release_show * f

    total_ns = day_df["y"].sum()
    return {
        "prompts_sent": int(prompts),
        "recovered": round(float(recovered), 1),
        "conflicts": round(float(conflicts), 1),
        "fill_rate": round(float(recovered / total_ns), 4) if total_ns else 0.0,
        "recovered_per_conflict": round(float(recovered / conflicts), 2) if conflicts else None,
    }


def run_policies(test: pd.DataFrame, p: np.ndarray, budget: float = 0.20, assumptions: dict | None = None) -> dict:
    a = {**DEFAULT_ASSUMPTIONS, **(assumptions or {})}
    df = pd.DataFrame({"appt_date": test["appt_date"].to_numpy(), "y": test["no_show"].to_numpy(), "p": np.asarray(p)})
    return {
        "budget": budget,
        "fill_probability": round(fill_probability(a), 4),
        "none": {"prompts_sent": 0, "recovered": 0.0, "conflicts": 0.0, "fill_rate": 0.0, "recovered_per_conflict": None},
        "random": _policy(df, budget, "random", a),
        "model": _policy(df, budget, "model", a),
        "everyone": _policy(df, 1.0, "model", a),
    }


def budget_curve(test: pd.DataFrame, p: np.ndarray, assumptions: dict | None = None) -> list[dict]:
    """Fill rate and double-bookings for budgets 5%..100%, model vs random."""
    a = {**DEFAULT_ASSUMPTIONS, **(assumptions or {})}
    df = pd.DataFrame({"appt_date": test["appt_date"].to_numpy(), "y": test["no_show"].to_numpy(), "p": np.asarray(p)})
    n = len(df)
    rows = []
    for b in np.round(np.arange(0.05, 1.0001, 0.05), 2):
        m, r = _policy(df, float(b), "model", a), _policy(df, float(b), "random", a)
        rows.append(
            {
                "budget": float(b),
                "model_fill_rate": m["fill_rate"],
                "random_fill_rate": r["fill_rate"],
                "model_double_bookings_per_100": round(100 * m["conflicts"] / n, 2),
                "random_double_bookings_per_100": round(100 * r["conflicts"] / n, 2),
            }
        )
    return rows
