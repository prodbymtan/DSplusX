# Slot Matcher

**Predict which patients won't show up, release their slots early, and refill them with nearby standby patients, before the appointment time is lost.**

Built for BU DS+X 2026. It fits Hackachusetts healthcare challenge **H3: Improving healthcare access and coordination**.

> All patients in the app are **synthetic** (Synthea). Hospital locations are **real** (MassGIS / MA Department of Public Health). The no-show model is trained on a real public dataset (Kaggle, Brazil 2016).

## Headline numbers

| | |
|---|---|
| No-show model (gradient boosting, test weeks) | **AUC 0.735**. The riskiest 20% of appointments contain **38%** of all no-shows |
| No-show slots refilled, same 20% outreach budget | **11.7% random → 22.4% model-targeted (1.9×)** |
| Refills per double-booking | **1.04 random → 2.53 model** |
| Residents within 2 mi of the clinic (Synthea, scaled to the 2020 Census) | **Boston (Kenmore) ~176,000 vs Greenfield ~7,000** |
| No-show slots refilled at a 2-mile radius | **Boston 22% vs Greenfield 1.4%** (8-mile ripple: 34% vs 5.3%) |

The model was trained on 67,360 appointments and evaluated once on 43,161 later appointments (May 24 to June 8, 2016), split by date so it's always tested on the future. The refill numbers are a simulation with stated assumptions; see [Honesty notes](#honesty-notes-say-these-before-a-judge-does).

---

## Quick start (about 5 minutes)

**You need:** Python **3.12 or 3.13** (`python3 --version`; on a Mac: `brew install python@3.12`) and Node **20.19+** (`node --version`; `brew install node@22`).

**Terminal 1: backend**
```bash
cd health-slot-app
python3.12 -m venv .venv            # or python3.13
source .venv/bin/activate            # Windows: .venv\Scripts\activate
pip install -r backend/requirements.txt
cd backend
uvicorn app.main:app --reload --port 8000
```

**Terminal 2: frontend**
```bash
cd health-slot-app/frontend
npm install
npm run dev
```
Open **http://localhost:5173**.

The trained model, the metrics and the Synthea extracts are already committed, so nothing needs training or downloading to run the demo.

### Single-process mode (for the projector laptop)
```bash
cd frontend && npm run build && cd ../backend
uvicorn app.main:app --port 8000
```
Open **http://localhost:8000**. FastAPI serves the built app itself: one process, one port.

### Faster ripple for the live demo
Offers widen their radius every 30 seconds by default. For a snappier demo:
```bash
OFFER_WINDOW_SECONDS=10 uvicorn app.main:app --port 8000
```

---

## 90-second demo script

1. **The problem** (top cards): the model is 1.9× better than random at choosing who to prompt. Point at "3 vs 0.12": the same system has far fewer standby patients in rural Massachusetts.
2. **The schedule:** each appointment has a no-show risk from the model. Red ones (≥36%) were asked to confirm.
3. Click **"No reply · release"** on the 10:00 AM row. Two phones light up at the same moment.
4. Click **Claim** on one phone. The dashboard shows "Filled by…" and the other phone shows "taken by someone else". *That's the race condition, handled by the database.*
5. Release the **1:00 PM** row and don't claim it. After one window the radius doubles and **Hassie** (2.4 mi away, travels ≤ 2 mi) gets the offer. *That's the ripple.*
6. Point at **Aline**: she's 0.2 mi away but her insurance isn't accepted, so she never gets offers.
7. Click **Reset demo** before the next judge.

---

## How it works

```
Kaggle no-show data ─► ml/src/train.py ─► model.pkl + metrics.json
Synthea MA residents ┐
MassGIS hospitals    ┴► ml/src/massachusetts.py ─► MA analysis + backend/app/seed_data/demo_seed.json

React (Vite) ◄── REST + WebSocket ──► FastAPI ──► SQLite (default) or Postgres
 ├ Clinic dashboard   risk.py scores today's schedule with model.pkl
 ├ 4 patient phones   offers.py: release → offer → ripple → claim
 ├ Map (offline SVG)  matching.py: distance, insurance, specialty, reliability
 └ Metrics panel      broadcaster.py: pushes offers / taken / expired
```

**Release.** A slot is released when a high-risk patient doesn't confirm, a patient no-shows, or a patient cancels.

**Offer.** Every eligible standby patient gets the offer at the same moment. To be eligible they must be within their travel radius, have insurance the clinic accepts, need the right specialty, and have standby turned on. Candidates are ranked 60% on reliability and 40% on closeness.

**Ripple.** If nobody claims within the offer window, every patient's radius doubles (two rounds by default). After that the slot expires.

**Claim.** The first tap wins, enforced by one atomic SQL statement:

```sql
UPDATE slots SET status='booked', ... WHERE id=:id AND status='open'
```

The database applies it atomically, so exactly one request succeeds and everyone else gets HTTP 409. `tests/test_flow.py` fires 20 simultaneous claims and checks there's exactly one winner, on both SQLite and Postgres 16.

The **WebSocket** messages are only hints. Each screen re-fetches its state over REST, so a dropped message can't leave a screen wrong.

---

## Project structure

```
health-slot-app/
├── ml/
│   ├── data/
│   │   ├── download.py               # Kaggle no-show CSV (checksum-verified mirror)
│   │   ├── synthea_ma_patients.csv   # 3,000 synthetic MA residents (no SSNs/addresses)
│   │   ├── ma_hospitals.csv          # 103 MassGIS / MA DPH hospitals
│   │   └── ma_primary_care_sites.csv # 456 MA primary-care sites (Synthea provider list)
│   ├── notebooks/
│   │   ├── 01_noshow_model.ipynb         # EDA, models, calibration, simulation (executed)
│   │   └── 02_massachusetts_context.ipynb # distance to care, standby density (executed)
│   ├── src/
│   │   ├── features.py       # features + leakage-safe patient history
│   │   ├── train.py          # date split, LogReg vs gradient boosting, writes artifacts
│   │   ├── simulate.py       # fill-rate simulation, model vs random
│   │   └── massachusetts.py  # Synthea + MassGIS analysis, builds the demo seed
│   └── artifacts/            # model.pkl, metrics.json, 6 slide-ready charts (.png)
├── backend/
│   ├── app/
│   │   ├── api/              # appointments, slots, patients, metrics, demo, ws
│   │   ├── core/             # config (env vars), database
│   │   ├── models/           # SQLAlchemy tables
│   │   ├── services/         # risk, matching, offers, broadcaster
│   │   ├── seed_data/demo_seed.json
│   │   ├── seed.py
│   │   └── main.py
│   ├── tests/test_flow.py    # 10 end-to-end tests incl. 20-way race
│   └── requirements.txt
├── frontend/                 # React 19 + Vite 8
│   └── src/{components,services}/ ...
├── synthea/generate.sh       # regenerate the synthetic population (optional, needs Java)
├── database/docker-compose.yml  # optional Postgres/PostGIS
└── README.md
```

---

## Rebuilding things (optional)

```bash
source .venv/bin/activate
pip install -r ml/requirements.txt
python ml/data/download.py          # 110,527 appointments, checksum verified
python ml/src/train.py              # retrains, reruns the simulation + MA analysis, rewrites the seed
jupyter notebook ml/notebooks/      # both notebooks are already executed with outputs
bash synthea/generate.sh            # new synthetic population (needs Java 17+)
```
Training is deterministic: rerunning reproduces identical metrics and the identical demo seed.

**Tests:** `cd backend && pytest -q`. To run them on Postgres: `TEST_DATABASE_URL=postgresql+psycopg://user@localhost:5432/dbname pytest -q`.

**Settings** (environment variables, or a `backend/.env` file):

| Variable | Default | Meaning |
|---|---|---|
| `DATABASE_URL` | SQLite file in `backend/` | e.g. `postgresql+psycopg://health:health@localhost:5432/health_slot` |
| `OFFER_WINDOW_SECONDS` | 30 | how long each offer round lasts |
| `RIPPLE_ROUNDS` | 2 | how many times the radius widens |
| `RADIUS_GROWTH` | 2.0 | radius multiplier per round |

---

## Data sources

| Data | What we use it for | Source / license |
|---|---|---|
| Kaggle *Medical Appointment No Shows* (110,527 appts, Vitória, Brazil, 2016) | Train and test the no-show model | Kaggle (joniarroba); fetched from Udacity's public mirror |
| **Synthea** synthetic Massachusetts population (3,000 residents) | Demo patients, distance-to-care analysis, standby density | MITRE Synthea, Apache-2.0. **Not real people.** |
| **MassGIS / MA DPH licensed hospitals** (103) | Hospitals on the map, distance to the nearest acute hospital | MassGIS ArcGIS service (listed on the Hackachusetts data portal) |
| Synthea's MA primary-care site list (456) | Distance to the nearest primary-care site | Synthea repository, Apache-2.0 |

Synthea's raw output includes fake SSNs, licenses and street addresses. `massachusetts.py prepare` drops them; only name, age, sex, town, coordinates, insurance, visit counts and two conditions are kept.

## Honesty notes (say these before a judge does)

- **The model data is from Brazil in 2016.** The patterns (lead time and history drive no-shows) are well documented elsewhere, but exact numbers won't transfer to Boston. A clinic would retrain on its own history.
- **The refill rates are simulated.** Confirmation rates (80% of attenders confirm, 10% of eventual no-shows still confirm) and standby acceptance (35%) are assumptions, listed in `metrics.json → assumptions`. The comparison between model and random holds under any setting, because both use the same assumptions.
- **The standby supply** anchors one assumption (3 standby patients within 2 mi of a Boston clinic) and scales it by Synthea population density. Rural counts rest on few synthetic residents, so treat them as order-of-magnitude.
- **The demo schedule is synthetic.** Patients come from Synthea, but booking lead time, past no-shows, SMS reminders, travel radius and reliability are scenario values, because Synthea doesn't simulate no-shows.
- **Distances are straight-line**, not drive time.
- **This is a prototype.** It has no authentication and no EHR integration. In production it would sit beside an EHR (Epic MyChart Fast Pass, Luma Health and others already do static waitlists) and connect via FHIR `Slot`/`Appointment` resources.

## Likely judge questions

- **"How is this different from Epic Fast Pass?"** Fast Pass offers a slot to waitlisted patients *after* someone cancels. Most no-shows never cancel, so those slots are lost. We act *before* that: the model flags likely no-shows, unconfirmed high-risk slots are released early, and the offer goes to people close enough to get there in time. It could run alongside Fast Pass, not instead of it.
- **"Race conditions?"** One conditional `UPDATE`, tested with 20 simultaneous claims on SQLite and Postgres.
- **"Isn't tracking location creepy?"** Patients set a home location and travel radius when they opt in. There's no live GPS tracking.
- **"What about rural patients?"** Notebook 02 shows that's exactly where a pure proximity system fails (1.4% vs 22%). The recommendation for rural clinics is to release earlier (hours ahead), widen the radius, or offer the slot as telehealth.
- **"Why gradient boosting?"** It beat logistic regression on the validation week (AUC 0.739 vs 0.733), and both were then scored once on test. Logistic regression is the interpretable fallback.

## Troubleshooting

- **`pip install` fails on numpy/pandas:** your Python is too old. Use 3.12 or 3.13.
- **Vite says Node is too old:** install Node 22 (`brew install node@22`).
- **Frontend shows "Can't reach the backend":** start uvicorn on port 8000. Vite proxies `/api` and `/ws` to `127.0.0.1:8000`; set `BACKEND_URL` to change it.
- **`risk_source` shows `fallback_rule`:** `model.pkl` didn't load (usually a scikit-learn version mismatch). Install the exact pins from `backend/requirements.txt`, or run `python ml/src/train.py`.
- **The demo is in a weird state:** click **Reset demo**, or delete `backend/health_slot.db` and restart.
