"""Massachusetts supporting analysis: Synthea synthetic residents + real MA facilities.

    python ml/src/massachusetts.py prepare --synthea-dir /path/to/synthea/output/csv   # optional, rebuilds extracts
    python ml/src/massachusetts.py analyze                                               # charts, metrics, demo seed

Data (all in ml/data/, small enough to commit):
  synthea_ma_patients.csv   3,000 living synthetic MA residents from Synthea (Apache-2.0).
                            NOT real people. Generated with synthea/generate.sh.
  ma_hospitals.csv          103 licensed hospitals, MassGIS / MA Department of Public Health.
  ma_primary_care_sites.csv 456 MA primary-care sites from Synthea's provider list.

What it answers:
  1. Access: how far do residents live from the nearest acute hospital / primary-care site, by county?
  2. Standby supply: how many people live within X miles of a Boston clinic vs a rural one?
     We anchor the simulation's "3 standby patients within 2 mi" assumption to a Boston clinic,
     and scale other places by Synthea population density. Then we rerun the fill-rate simulation.
  3. Demo seed: builds backend/app/seed_data/demo_seed.json from Synthea residents near the clinic.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
from simulate import DEFAULT_ASSUMPTIONS, run_policies  # noqa: E402

ML_DIR = Path(__file__).resolve().parents[1]
DATA = ML_DIR / "data"
ARTIFACTS = ML_DIR / "artifacts"
SEED_OUT = ML_DIR.parent / "backend" / "app" / "seed_data" / "demo_seed.json"

MA_POPULATION = 7_029_917  # 2020 U.S. Census, Massachusetts
REFERENCE_DATE = pd.Timestamp("2026-10-24")  # Synthea was run with -r 20261024
MASSGIS_URL = (
    "https://arcgisserver.digital.mass.gov/arcgisserver/rest/services/AGOL/Hospitals/MapServer/0/query"
    "?where=1%3D1&outFields=*&returnGeometry=true&outSR=4326&f=json"
)

# Demo clinic: a fictional practice placed at Kenmore Square, Boston.
CLINIC = {
    "name": "Kenmore Primary Care (demo clinic)",
    "lat": 42.3489,
    "lng": -71.0951,
    "specialty": "primary_care",
    # Humana is deliberately left out so the demo can show insurance filtering.
    "accepted_insurance": [
        "Medicare", "Medicaid", "Dual Eligible", "Blue Cross Blue Shield",
        "UnitedHealthcare", "Aetna", "Cigna Health", "Anthem", "NO_INSURANCE",
    ],
}
SITES = {
    "boston": {"label": "Boston (Kenmore)", "lat": 42.3489, "lng": -71.0951},
    "rural": {"label": "Greenfield (Franklin Co.)", "lat": 42.5876, "lng": -72.5995},
}
ANCHOR = {"site": "boston", "radius_miles": 2, "standby_patients": DEFAULT_ASSUMPTIONS["standby_patients_in_radius"]}
RIPPLE_RADIUS = 8  # 2 mi default, doubled twice (backend: RIPPLE_ROUNDS=2, RADIUS_GROWTH=2)


def haversine(lat1, lon1, lat2, lon2):
    lat1, lon1, lat2, lon2 = map(np.radians, (lat1, lon1, lat2, lon2))
    a = np.sin((lat2 - lat1) / 2) ** 2 + np.cos(lat1) * np.cos(lat2) * np.sin((lon2 - lon1) / 2) ** 2
    return 2 * 3958.8 * np.arcsin(np.sqrt(a))


def clean_name(s: str) -> str:
    """Synthea appends digits to names (Wilfredo622). Strip them."""
    return re.sub(r"\d+", "", str(s)).strip()


# ---------------------------------------------------------------- prepare

def prepare(synthea_dir: Path, providers_csv: Path | None, massgis_json: Path | None) -> None:
    """Turn raw Synthea CSV output into one small, privacy-safe resident table."""
    p = pd.read_csv(synthea_dir / "patients.csv")
    p = p[p["DEATHDATE"].isna()].copy()
    enc = pd.read_csv(synthea_dir / "encounters.csv", usecols=["START", "PATIENT", "ENCOUNTERCLASS"])
    enc["START"] = pd.to_datetime(enc["START"]).dt.tz_localize(None)
    cond = pd.read_csv(synthea_dir / "conditions.csv", usecols=["PATIENT", "DESCRIPTION", "STOP"])
    payers = pd.read_csv(synthea_dir / "payers.csv", usecols=["Id", "NAME"]).set_index("Id")["NAME"]
    trans = pd.read_csv(synthea_dir / "payer_transitions.csv", usecols=["PATIENT", "START_DATE", "END_DATE", "PAYER"])

    primary = enc[enc["ENCOUNTERCLASS"].isin(["wellness", "ambulatory"]) & (enc["START"] <= REFERENCE_DATE)]
    last_year = primary[primary["START"] > REFERENCE_DATE - pd.Timedelta(days=365)].groupby("PATIENT").size()
    last_90 = primary[primary["START"] > REFERENCE_DATE - pd.Timedelta(days=90)].groupby("PATIENT").size()

    active = cond[cond["STOP"].isna()]
    htn = set(active.loc[active["DESCRIPTION"].str.contains("hypertension", case=False), "PATIENT"])
    dm = set(active.loc[active["DESCRIPTION"].str.contains("diabetes mellitus", case=False), "PATIENT"])

    trans["START_DATE"] = pd.to_datetime(trans["START_DATE"]).dt.tz_localize(None)
    trans["END_DATE"] = pd.to_datetime(trans["END_DATE"]).dt.tz_localize(None)
    current = trans[(trans["START_DATE"] <= REFERENCE_DATE) & (trans["END_DATE"].isna() | (trans["END_DATE"] >= REFERENCE_DATE))]
    current = current.sort_values("START_DATE").groupby("PATIENT")["PAYER"].last().map(payers)

    out = pd.DataFrame(
        {
            "synthea_id": p["Id"],
            "first_name": p["FIRST"].map(clean_name),
            "last_name": p["LAST"].map(clean_name),
            "age": ((REFERENCE_DATE - pd.to_datetime(p["BIRTHDATE"])).dt.days // 365).astype(int),
            "gender": p["GENDER"],
            "city": p["CITY"],
            "county": p["COUNTY"].str.replace(" County", "", regex=False),
            "lat": p["LAT"].round(5),
            "lon": p["LON"].round(5),
            "insurance": p["Id"].map(current).fillna("NO_INSURANCE"),
            "primary_visits_last_year": p["Id"].map(last_year).fillna(0).astype(int),
            "primary_visits_last_90d": p["Id"].map(last_90).fillna(0).astype(int),
            "hypertension": p["Id"].isin(htn).astype(int),
            "diabetes": p["Id"].isin(dm).astype(int),
        }
    )
    # SSN, driver's license, passport, street address and income are deliberately dropped.
    out.to_csv(DATA / "synthea_ma_patients.csv", index=False)
    print(f"Wrote {len(out):,} synthetic residents to {DATA / 'synthea_ma_patients.csv'}")

    if providers_csv:
        f = pd.read_csv(providers_csv, dtype=str)
        f = f[f["state"] == "MA"][["name", "city", "lat", "lon"]].copy()
        f["name"] = f["name"].str.title()
        f.to_csv(DATA / "ma_primary_care_sites.csv", index=False)
        print(f"Wrote {len(f)} MA primary-care sites")

    if massgis_json:
        feats = json.loads(Path(massgis_json).read_text())["features"]
        rows = []
        for x in feats:
            a, g = x["attributes"], x.get("geometry") or {}
            if "x" not in g:
                continue
            rows.append(
                {
                    "name": a["FACILITY_NAME"],
                    "type": a["FACILITY_TYPE"],
                    "municipality": str(a["MUNICIPALITY"]).title(),
                    "county": str(a["COUNTY"]).title(),
                    "lat": round(g["y"], 6),
                    "lon": round(g["x"], 6),
                    "total_beds": a.get("TOTAL_BEDS"),
                    "icu_beds": a.get("ICU"),
                    "emergency_dept": a.get("EMERGENCY_DEPT"),
                }
            )
        pd.DataFrame(rows).to_csv(DATA / "ma_hospitals.csv", index=False)
        print(f"Wrote {len(rows)} MA hospitals")


# ---------------------------------------------------------------- analyze

def load_tables():
    residents = pd.read_csv(DATA / "synthea_ma_patients.csv")
    hospitals = pd.read_csv(DATA / "ma_hospitals.csv")
    sites = pd.read_csv(DATA / "ma_primary_care_sites.csv")
    return residents, hospitals, sites


def nearest_distance(lat, lon, targets: pd.DataFrame) -> np.ndarray:
    d = haversine(lat[:, None], lon[:, None], targets["lat"].to_numpy()[None, :], targets["lon"].to_numpy()[None, :])
    return d.min(axis=1)


def access_by_county(residents, hospitals, sites) -> pd.DataFrame:
    acute = hospitals[hospitals["type"] == "Acute Hospital"]
    lat, lon = residents["lat"].to_numpy(), residents["lon"].to_numpy()
    r = residents.assign(
        miles_to_acute_hospital=nearest_distance(lat, lon, acute),
        miles_to_primary_care_site=nearest_distance(lat, lon, sites),
    )
    g = r.groupby("county").agg(
        synthetic_residents=("synthea_id", "size"),
        median_miles_to_hospital=("miles_to_acute_hospital", "median"),
        share_over_10mi_from_hospital=("miles_to_acute_hospital", lambda s: (s > 10).mean()),
        median_miles_to_primary_care=("miles_to_primary_care_site", "median"),
    )
    return g.sort_values("median_miles_to_hospital", ascending=False).round(3)


def residents_within(residents, lat, lng, radii=(1, 2, 4, 8, 16)) -> dict:
    """Radii double, matching the app's ripple (2 mi -> 4 -> 8)."""
    d = haversine(residents["lat"].to_numpy(), residents["lon"].to_numpy(), lat, lng)
    scale = MA_POPULATION / len(residents)
    return {r: {"synthetic": int((d <= r).sum()), "estimated_residents": int(round((d <= r).sum() * scale))} for r in radii}


def standby_estimates(residents) -> dict:
    """Scale the anchor assumption (3 standby patients within 2 mi in Boston) by population density."""
    within = {k: residents_within(residents, s["lat"], s["lng"]) for k, s in SITES.items()}
    anchor_pop = within[ANCHOR["site"]][ANCHOR["radius_miles"]]["estimated_residents"]
    if anchor_pop == 0:
        raise ValueError(
            "No synthetic residents within 2 mi of the Boston clinic; the population is too small. "
            "Rerun synthea/generate.sh with POPULATION=3000 or more."
        )
    per_resident = ANCHOR["standby_patients"] / anchor_pop
    out = {}
    for k, s in SITES.items():
        lam = {r: round(v["estimated_residents"] * per_resident, 3) for r, v in within[k].items()}
        out[k] = {**s, "residents_within": within[k], "standby_patients_within": lam}
    return out


def test_predictions():
    """Model predictions on the held-out test weeks (same as train.py)."""
    import joblib
    from features import FEATURES, load_dataset, time_split

    bundle = joblib.load(ARTIFACTS / "model.pkl")
    _, _, test = time_split(load_dataset())
    return test, bundle["pipeline"].predict_proba(test[FEATURES])[:, 1]


def fill_by_place(estimates: dict, test, p) -> dict:
    res = {}
    for k, e in estimates.items():
        lam = e["standby_patients_within"]
        at = {}
        for r in (2, RIPPLE_RADIUS):
            a = {**DEFAULT_ASSUMPTIONS, "standby_patients_in_radius": lam[r]}  # KeyError if r wasn't computed
            sim = run_policies(test, p, budget=0.20, assumptions=a)
            at[r] = {"standby_patients": a["standby_patients_in_radius"], "fill_probability": sim["fill_probability"], "fill_rate_model": sim["model"]["fill_rate"]}
        res[k] = at
    return res


def build_seed(residents, hospitals) -> dict:
    """Pick synthetic residents near the clinic for the demo phones and schedule."""
    c = CLINIC
    r = residents.assign(miles=haversine(residents["lat"].to_numpy(), residents["lon"].to_numpy(), c["lat"], c["lng"]))
    adults = r[(r["age"] >= 18) & (r["age"] <= 85)].sort_values(["miles", "synthea_id"])

    def pick(df, used, fallback=None):
        """First unused resident in df; if none, the first unused one in fallback (nearest adults)."""
        for source in (df, fallback if fallback is not None else adults):
            rest = source[~source["synthea_id"].isin(used)]
            if not rest.empty:
                row = rest.iloc[0]
                used.add(row["synthea_id"])
                return row
        raise ValueError("Not enough synthetic adults near the clinic. Regenerate with a larger POPULATION.")

    used: set = set()
    accepted = set(c["accepted_insurance"])
    close = adults[(adults["miles"] >= 0.3) & (adults["miles"] <= 1.6) & adults["insurance"].isin(accepted)]
    far = adults[(adults["miles"] >= 2.4) & (adults["miles"] <= 3.6) & adults["insurance"].isin(accepted)]
    p1, p2 = pick(close, used), pick(close, used)
    # Prefer someone 2.4-3.6 mi away (outside a 2 mi radius until the ripple widens it).
    p3 = pick(far, used, fallback=adults[adults["miles"] > 2.0])
    # Someone close by whose plan the clinic doesn't take (shows insurance filtering).
    out_net = adults[(adults["miles"] <= 2) & ~adults["insurance"].isin(accepted)]
    if out_net.empty:  # fall back: give a close resident an out-of-network plan
        p4 = pick(close, used).copy()
        p4["insurance"] = "Humana"
    else:
        p4 = pick(out_net, used)

    def phone(row, radius, reliability):
        return {
            "name": f"{row['first_name']} {row['last_name'][0]}.",
            "synthea_id": row["synthea_id"],
            "age": int(row["age"]),
            "gender": row["gender"],
            "lat": float(row["lat"]),
            "lng": float(row["lon"]),
            "city": row["city"],
            "insurance": row["insurance"],
            "radius_miles": radius,
            "reliability": reliability,
        }

    standby = [phone(p1, 3.0, 0.95), phone(p2, 3.0, 0.85), phone(p3, 2.0, 0.90), phone(p4, 3.0, 0.92)]

    # Today's schedule: 10 synthetic residents within 5 miles. Demographics, conditions and
    # visit counts come from Synthea. Booking lead time, past no-shows and SMS are SCENARIO
    # values (Synthea doesn't simulate no-shows), chosen to give a realistic spread of risk.
    pool = adults[(adults["miles"] <= 5) & ~adults["synthea_id"].isin(used)].head(10)
    scenario = [
        # start, lead_days, booked_hour, prior_noshows (capped by visit count), sms
        ("09:00", 0, 8, 0, 0),
        ("09:30", 3, 10, 0, 0),
        ("10:00", 45, 14, 2, 1),
        ("10:30", 7, 9, 0, 1),
        ("11:00", 1, 16, 0, 0),
        ("13:00", 38, 11, 1, 1),
        ("13:30", 14, 10, 0, 1),
        ("14:00", 60, 15, 2, 1),
        ("14:30", 2, 9, 0, 0),
        ("15:30", 28, 13, 1, 1),
    ]
    schedule = []
    for (start, lead, hour, noshows, sms), (_, row) in zip(scenario, pool.iterrows()):
        # The training data covered ~6 weeks of history, so keep counts in that range.
        prior = min(max(int(row["primary_visits_last_90d"]), noshows), 6)
        schedule.append(
            {
                "start": start,
                "label": f"{row['first_name']} {row['last_name'][0]}.",
                "synthea_id": row["synthea_id"],
                "age": int(row["age"]),
                "gender": row["gender"],
                "hypertension": int(row["hypertension"]),
                "diabetes": int(row["diabetes"]),
                "prior_appts": prior,
                "prior_noshows": noshows,
                "lead_days": lead,
                "booked_hour": hour,
                "sms_received": sms,
                "duration_min": 30,
            }
        )

    near_h = hospitals.assign(miles=haversine(hospitals["lat"].to_numpy(), hospitals["lon"].to_numpy(), c["lat"], c["lng"]))
    near_h = near_h[near_h["type"].isin(["Acute Hospital", "Satellite Emergency Facility"])].sort_values("miles").head(12)
    return {
        "clinic": c,
        "standby": standby,
        "schedule": schedule,
        "hospitals": [
            {"name": h["name"], "lat": float(h["lat"]), "lng": float(h["lon"]), "type": h["type"], "municipality": h["municipality"], "total_beds": None if pd.isna(h["total_beds"]) else int(h["total_beds"])}
            for _, h in near_h.iterrows()
        ],
        "sources": {
            "patients": "Synthea synthetic Massachusetts residents (not real people). Apache-2.0.",
            "hospitals": "MassGIS / MA Department of Public Health licensed hospitals.",
            "scenario_fields": ["lead_days", "booked_hour", "prior_noshows", "sms_received", "radius_miles", "reliability"],
        },
    }


def analyze(make_charts: bool = True) -> dict:
    residents, hospitals, sites = load_tables()
    access = access_by_county(residents, hospitals, sites)
    estimates = standby_estimates(residents)
    test, p = test_predictions()
    fills = fill_by_place(estimates, test, p)

    block = {
        "synthetic_residents": int(len(residents)),
        "anchor": ANCHOR,
        "ripple_radius_miles": RIPPLE_RADIUS,
        "boston": {
            "label": SITES["boston"]["label"],
            "residents_within_2mi": estimates["boston"]["residents_within"][2]["estimated_residents"],
            "standby_within_2mi": round(estimates["boston"]["standby_patients_within"][2], 1),
            "fill": fills["boston"],
        },
        "rural": {
            "label": SITES["rural"]["label"],
            "residents_within_2mi": estimates["rural"]["residents_within"][2]["estimated_residents"],
            "standby_within_2mi": round(estimates["rural"]["standby_patients_within"][2], 2),
            "fill": fills["rural"],
        },
        "access_by_county": access.reset_index().to_dict(orient="records"),
        "estimates": estimates,
        "sources": {
            "residents": "Synthea synthetic Massachusetts population, 3,000 living residents, scaled to 2020 Census (7,029,917).",
            "hospitals": "MassGIS / MA DPH licensed hospitals (103 facilities; 70 acute).",
            "primary_care_sites": "Synthea's Massachusetts primary-care site list (456 sites).",
        },
        "caveats": [
            "Synthetic residents follow census town populations but are not real people.",
            "Rural counts come from few synthetic residents; rerun Synthea with more people for tighter numbers.",
            "Standby supply is anchored to an assumption (3 within 2 mi in Boston) and scaled by density.",
        ],
    }

    metrics_path = ARTIFACTS / "metrics.json"
    metrics = json.loads(metrics_path.read_text())
    metrics["massachusetts"] = block
    metrics_path.write_text(json.dumps(metrics, indent=2))

    seed = build_seed(residents, hospitals)
    SEED_OUT.parent.mkdir(parents=True, exist_ok=True)
    SEED_OUT.write_text(json.dumps(seed, indent=2))

    if make_charts:
        charts(access, estimates, fills)

    print(json.dumps({k: block[k] for k in ("boston", "rural")}, indent=2))
    print(access.head(6).to_string())
    print(f"Seed: {len(seed['standby'])} standby, {len(seed['schedule'])} appointments, {len(seed['hospitals'])} hospitals -> {SEED_OUT}")
    return block


def charts(access: pd.DataFrame, estimates: dict, fills: dict) -> None:
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    plt.rcParams.update({"axes.spines.top": False, "axes.spines.right": False})
    a = access[access["synthetic_residents"] >= 10].sort_values("median_miles_to_hospital")
    fig, ax = plt.subplots(figsize=(7, 4))
    ax.barh(a.index, a["median_miles_to_hospital"], color="#534AB7")
    ax.set_xlabel("Median miles to nearest acute hospital")
    ax.set_title("Distance to care by county (synthetic MA residents)")
    plt.tight_layout()
    plt.savefig(ARTIFACTS / "ma_distance_by_county.png", dpi=160)
    plt.close(fig)

    fig, ax = plt.subplots(figsize=(7, 3.8))
    for k, color in (("boston", "#534AB7"), ("rural", "#D85A30")):
        radii = sorted(estimates[k]["residents_within"])
        ax.plot(radii, [estimates[k]["residents_within"][r]["estimated_residents"] for r in radii], "o-", color=color, label=estimates[k]["label"])
    ax.set_yscale("log")
    ax.set_xlabel("Radius around clinic (miles)")
    ax.set_ylabel("Residents within radius (log)")
    ax.set_title("How many people live close enough to fill a last-minute slot?")
    ax.legend()
    plt.tight_layout()
    plt.savefig(ARTIFACTS / "ma_standby_density.png", dpi=160)
    plt.close(fig)


def main() -> None:
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    pr = sub.add_parser("prepare")
    pr.add_argument("--synthea-dir", type=Path, required=True)
    pr.add_argument("--providers-csv", type=Path, help="Synthea src/main/resources/providers/primary_care_facilities.csv")
    pr.add_argument("--massgis-json", type=Path, help=f"Saved response of {MASSGIS_URL}")
    sub.add_parser("analyze")
    args = ap.parse_args()
    if args.cmd == "prepare":
        prepare(args.synthea_dir, args.providers_csv, args.massgis_json)
    else:
        analyze()


if __name__ == "__main__":
    main()
