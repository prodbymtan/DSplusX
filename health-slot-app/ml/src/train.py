"""Train the no-show model and save it for the backend.

    python ml/src/train.py

1. Compare logistic regression vs gradient boosting on a validation week.
2. Refit the winner on train+val.
3. Evaluate once on the held-out future weeks (test).
4. Run the fill-rate simulation on the test predictions.
5. Write ml/artifacts/model.pkl and ml/artifacts/metrics.json.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import brier_score_loss, roc_auc_score
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

sys.path.insert(0, str(Path(__file__).resolve().parent))
from features import (  # noqa: E402
    BINARY_FEATURES,
    CATEGORICAL_FEATURES,
    FEATURES,
    NUMERIC_FEATURES,
    TARGET,
    load_dataset,
    time_split,
)
from simulate import DEFAULT_ASSUMPTIONS, budget_curve, catch_rate, run_policies  # noqa: E402

ARTIFACTS = Path(__file__).resolve().parents[1] / "artifacts"
SEED = 42


def make_models() -> dict[str, Pipeline]:
    """Two candidates: an interpretable baseline and a stronger tree model."""
    logreg = Pipeline(
        [
            (
                "prep",
                ColumnTransformer(
                    [
                        ("num", StandardScaler(), NUMERIC_FEATURES),
                        ("bin", "passthrough", BINARY_FEATURES),
                        ("cat", OneHotEncoder(handle_unknown="ignore"), CATEGORICAL_FEATURES),
                    ]
                ),
            ),
            ("clf", LogisticRegression(max_iter=2000)),
        ]
    )
    # HistGradientBoosting is scikit-learn's LightGBM-style model. It needs no extra
    # install (LightGBM needs `brew install libomp` on Macs, which is a hackathon trap).
    hgb = Pipeline(
        [
            (
                "prep",
                ColumnTransformer(
                    [
                        ("num", "passthrough", NUMERIC_FEATURES + BINARY_FEATURES),
                        ("cat", OneHotEncoder(handle_unknown="ignore", sparse_output=False), CATEGORICAL_FEATURES),
                    ]
                ),
            ),
            (
                "clf",
                HistGradientBoostingClassifier(
                    learning_rate=0.05,
                    max_iter=400,
                    max_leaf_nodes=31,
                    min_samples_leaf=50,
                    l2_regularization=1.0,
                    early_stopping=True,
                    validation_fraction=0.15,
                    random_state=SEED,
                ),
            ),
        ]
    )
    return {"logistic_regression": logreg, "gradient_boosting": hgb}


def evaluate(y: np.ndarray, p: np.ndarray) -> dict:
    return {
        "auc": round(float(roc_auc_score(y, p)), 4),
        "brier": round(float(brier_score_loss(y, p)), 4),
        "top20_catch_rate": round(float(catch_rate(y, p, 0.20)), 4),
    }


def main() -> dict:
    ARTIFACTS.mkdir(parents=True, exist_ok=True)
    data = load_dataset()
    train, val, test = time_split(data)

    # Step 1: model selection on the validation week only.
    selection = {}
    for name, model in make_models().items():
        model.fit(train[FEATURES], train[TARGET])
        selection[name] = evaluate(val[TARGET].to_numpy(), model.predict_proba(val[FEATURES])[:, 1])
        print(f"[val] {name}: {selection[name]}")
    best_name = max(selection, key=lambda n: selection[n]["auc"])
    print(f"Selected: {best_name}")

    # Step 2: refit both on train+val (so we can report both on test), keep the winner.
    trainval = pd.concat([train, val])
    test_results, test_preds, fitted = {}, {}, {}
    for name, model in make_models().items():
        model.fit(trainval[FEATURES], trainval[TARGET])
        fitted[name] = model
        test_preds[name] = model.predict_proba(test[FEATURES])[:, 1]
        test_results[name] = evaluate(test[TARGET].to_numpy(), test_preds[name])
        print(f"[test] {name}: {test_results[name]}")

    model = fitted[best_name]
    y_test = test[TARGET].to_numpy()
    p_test = test_preds[best_name]

    # "High risk" = the top 20% of scores on the test weeks. The dashboard uses this cutoff.
    high_risk_threshold = float(np.quantile(p_test, 0.80))

    # Step 3: simulation on the real test predictions.
    sim = run_policies(test, p_test, budget=0.20, assumptions=DEFAULT_ASSUMPTIONS)
    curve = budget_curve(test, p_test, assumptions=DEFAULT_ASSUMPTIONS)

    days = test["appt_date"].nunique()
    metrics = {
        "model_name": best_name,
        "auc": test_results[best_name]["auc"],
        "brier": test_results[best_name]["brier"],
        "top20_catch_rate": test_results[best_name]["top20_catch_rate"],
        "fill_rate_baseline": sim["random"]["fill_rate"],
        "fill_rate_ours": sim["model"]["fill_rate"],
        "slots_recovered": sim["model"]["recovered"],
        "slots_recovered_per_100_appts": round(100 * sim["model"]["recovered"] / len(test), 2),
        "double_bookings_per_100_appts": round(100 * sim["model"]["conflicts"] / len(test), 2),
        "high_risk_threshold": round(high_risk_threshold, 4),
        "base_noshow_rate": round(float(y_test.mean()), 4),
        "n_train": int(len(trainval)),
        "n_test": int(len(test)),
        "test_days": int(days),
        "test_period": [str(test["appt_date"].min().date()), str(test["appt_date"].max().date())],
        "validation": selection,
        "test_by_model": test_results,
        "policies": sim,
        "budget_curve": curve,
        "assumptions": DEFAULT_ASSUMPTIONS,
        "definitions": {
            "fill_rate": "Share of no-show slots that get refilled by a standby patient (expected value).",
            "fill_rate_baseline": "Same outreach budget (20% of appointments), but patients picked at random: no model.",
            "fill_rate_ours": "Same budget, patients picked by highest predicted no-show risk.",
            "double_bookings": "Released slot was refilled but the original patient showed up anyway.",
            "top20_catch_rate": "Share of all no-shows that fall in the top 20% of predicted risk.",
        },
    }

    joblib.dump(
        {"pipeline": model, "features": FEATURES, "high_risk_threshold": high_risk_threshold, "model_name": best_name},
        ARTIFACTS / "model.pkl",
    )
    (ARTIFACTS / "metrics.json").write_text(json.dumps(metrics, indent=2))
    print(json.dumps({k: metrics[k] for k in ["model_name", "auc", "top20_catch_rate", "fill_rate_baseline", "fill_rate_ours", "high_risk_threshold"]}, indent=2))

    # Refresh the Massachusetts block (it depends on this model) and the demo seed.
    try:
        import massachusetts

        print("\nUpdating Massachusetts analysis and demo seed...")
        massachusetts.analyze()
    except FileNotFoundError as exc:
        print(f"Skipped Massachusetts analysis ({exc}).")
    return metrics


if __name__ == "__main__":
    main()
