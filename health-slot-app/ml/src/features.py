"""Load the Kaggle "Medical Appointment No Shows" data and build model features.

Every feature here is something a clinic would know *before* the appointment,
so the same function works for training and for scoring a live schedule.
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

DATA_PATH = Path(__file__).resolve().parents[1] / "data" / "noshow.csv"

# Columns the model sees. Order matters only for readability; the pipeline
# selects by name.
NUMERIC_FEATURES = [
    "lead_days",
    "age",
    "prior_appts",
    "prior_noshows",
    "prior_noshow_rate",
    "booked_hour",
]
BINARY_FEATURES = [
    "same_day",
    "is_female",
    "scholarship",
    "hypertension",
    "diabetes",
    "alcoholism",
    "disability",
    "sms_received",
    "first_visit",
]
CATEGORICAL_FEATURES = ["appt_weekday"]
FEATURES = NUMERIC_FEATURES + BINARY_FEATURES + CATEGORICAL_FEATURES
TARGET = "no_show"


def load_raw(path: str | Path = DATA_PATH) -> pd.DataFrame:
    """Read the CSV and fix the dataset's known traps."""
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(
            f"{path} not found. Run `python ml/data/download.py` or download "
            "KaggleV2-May-2016.csv from Kaggle and save it as ml/data/noshow.csv."
        )
    df = pd.read_csv(path)

    # Trap 1: the label is backwards. "No" means the patient SHOWED UP.
    df[TARGET] = (df["No-show"] == "Yes").astype(int)

    # AppointmentDay has a date but no time (always 00:00). ScheduledDay has a real time.
    df["appt_date"] = pd.to_datetime(df["AppointmentDay"]).dt.tz_localize(None).dt.normalize()
    df["booked_at"] = pd.to_datetime(df["ScheduledDay"]).dt.tz_localize(None)

    # Trap 2: a few rows are booked after the appointment date, plus one age of -1.
    lead = (df["appt_date"] - df["booked_at"].dt.normalize()).dt.days
    df = df[(lead >= 0) & (df["Age"] >= 0)].copy()

    df = df.rename(
        columns={
            "PatientId": "patient_id",
            "AppointmentID": "appointment_id",
            "Age": "age_raw",
            "Scholarship": "scholarship",
            "Hipertension": "hypertension",  # original column is misspelled
            "Diabetes": "diabetes",
            "Alcoholism": "alcoholism",
            "Handcap": "handcap",  # misspelled in the source; 0-4 count
            "SMS_received": "sms_received",
            "Neighbourhood": "neighbourhood",
        }
    )
    return df.reset_index(drop=True)


def add_history(df: pd.DataFrame) -> pd.DataFrame:
    """Add each patient's no-show history using ONLY earlier appointment days.

    Appointments on the same day are not counted as history for each other,
    so nothing from the future (or the same day) leaks into a row.
    """
    df = df.sort_values(["patient_id", "appt_date", "appointment_id"]).copy()

    # Collapse to one row per patient-day, then shift so each day only sees prior days.
    daily = (
        df.groupby(["patient_id", "appt_date"])[TARGET]
        .agg(day_appts="size", day_noshows="sum")
        .reset_index()
        .sort_values(["patient_id", "appt_date"])
    )
    grp = daily.groupby("patient_id")
    daily["prior_appts"] = grp["day_appts"].cumsum() - daily["day_appts"]
    daily["prior_noshows"] = grp["day_noshows"].cumsum() - daily["day_noshows"]

    df = df.merge(
        daily[["patient_id", "appt_date", "prior_appts", "prior_noshows"]],
        on=["patient_id", "appt_date"],
        how="left",
    )
    return df


def build_features(df: pd.DataFrame) -> pd.DataFrame:
    """Turn raw-ish columns into model features.

    Expects columns: appt_date, booked_at, age_raw, Gender, scholarship,
    hypertension, diabetes, alcoholism, handcap, sms_received,
    prior_appts, prior_noshows. Used for both training data and live schedules.
    """
    out = pd.DataFrame(index=df.index)
    lead = (pd.to_datetime(df["appt_date"]).dt.normalize() - pd.to_datetime(df["booked_at"]).dt.normalize()).dt.days
    out["lead_days"] = lead.clip(lower=0, upper=180).astype(float)
    out["same_day"] = (lead <= 0).astype(int)
    out["age"] = df["age_raw"].clip(lower=0, upper=100).astype(float)
    out["booked_hour"] = pd.to_datetime(df["booked_at"]).dt.hour.astype(float)
    out["appt_weekday"] = pd.to_datetime(df["appt_date"]).dt.day_of_week.astype(int).astype(str)

    prior_appts = df["prior_appts"].fillna(0).astype(float)
    prior_noshows = df["prior_noshows"].fillna(0).astype(float)
    out["prior_appts"] = prior_appts
    out["prior_noshows"] = prior_noshows
    # Smoothed rate: patients with no history sit near the overall average (~20%)
    # instead of looking perfectly reliable.
    out["prior_noshow_rate"] = (prior_noshows + 0.2 * 2) / (prior_appts + 2)
    out["first_visit"] = (prior_appts == 0).astype(int)

    out["is_female"] = (df["Gender"] == "F").astype(int)
    out["scholarship"] = df["scholarship"].astype(int)
    out["hypertension"] = df["hypertension"].astype(int)
    out["diabetes"] = df["diabetes"].astype(int)
    out["alcoholism"] = df["alcoholism"].astype(int)
    out["disability"] = (df["handcap"] > 0).astype(int)
    out["sms_received"] = df["sms_received"].astype(int)
    return out[FEATURES]


def load_dataset(path: str | Path = DATA_PATH) -> pd.DataFrame:
    """Raw data + history + features + label, sorted by appointment date."""
    df = add_history(load_raw(path))
    feats = build_features(df)
    full = pd.concat([df[["appointment_id", "patient_id", "appt_date", "neighbourhood", TARGET]], feats], axis=1)
    return full.sort_values(["appt_date", "appointment_id"]).reset_index(drop=True)


def time_split(df: pd.DataFrame, val_start: str = "2016-05-16", test_start: str = "2016-05-24"):
    """Split by appointment date so the model is always tested on the future.

    Returns (train, val, test). Train+val are used to pick a model; the final
    model is refit on train+val and evaluated once on test.
    """
    val_start, test_start = pd.Timestamp(val_start), pd.Timestamp(test_start)
    train = df[df["appt_date"] < val_start]
    val = df[(df["appt_date"] >= val_start) & (df["appt_date"] < test_start)]
    test = df[df["appt_date"] >= test_start]
    return train, val, test


if __name__ == "__main__":
    data = load_dataset()
    tr, va, te = time_split(data)
    print(f"rows={len(data):,} train={len(tr):,} val={len(va):,} test={len(te):,}")
    print(f"no-show rate: {data[TARGET].mean():.3f}")
    print(data[FEATURES].describe().T[["mean", "min", "max"]])
