# HealthSlot — System Architecture

## Overview

HealthSlot recovers unused clinic capacity (no-shows + late cancellations) by
matching nearby standby patients to open slots in real time — treating
healthcare scheduling like a rideshare dispatch system.

---

## Core Event Flow

```
EHR System (Epic/Cerner)
        │
        │  FHIR Subscription webhook
        ▼
POST /api/v1/webhooks/fhir
        │
        ▼
fhir_integration.py
  ↳ Maps FHIR Appointment.status → internal SlotStatus
  ↳ If status → "available": triggers matching_engine
        │
        ▼
matching_engine.trigger_slot_broadcast()
  1. Load clinic PostGIS coordinates (ST_X/ST_Y)
  2. Pull all standby users from Redis (O(n) scan)
  3. Haversine filter → nearest N patients within radius
  4. Load FCM tokens from PostgreSQL
  5. FCM batch send (push_notifications.py)
  6. Redis PUBLISH → slot_events channel
        │
        ├──► Mobile App (push notification)
        │      Patient sees: "⚡ 20-min slot at Boston General — 3 min away"
        │
        └──► WebSocket clients (ws.py)
               Patient sees live card with 60-second countdown
                       │
                       ▼
              POST /api/v1/bookings/claim
                       │
                       ▼
              Redis SET NX (atomic lock, 30s TTL)
              ← First caller wins → slot status = "locked"
              ← All others → 409 Conflict
                       │
                       ▼
              POST /api/v1/bookings/confirm (within 30s)
                       │
                       ▼
              Booking record created, slot status = "booked"
              Redis lock released
              Confirmation push sent to patient
```

---

## Race Condition Prevention

The double-booking problem is solved at the Redis layer, not the DB layer:

```
Patient A ──► Redis SET NX slot:uuid → "userA"  ✓ ACQUIRED
Patient B ──► Redis SET NX slot:uuid → "userA"  ✗ KEY EXISTS → 409

After 30s with no confirm: Celery task calls release_expired_lock()
  → Redis DEL slot:uuid
  → DB slot.status = "available"
  → Re-triggers broadcast to next nearest patient
```

This is faster and more reliable than DB-level row locking for sub-second
concurrent requests.

---

## Database Schema (PostGIS)

```
users ──────────────────────────────────────── bookings
  id UUID PK                                    id UUID PK
  email VARCHAR UNIQUE                          slot_id UUID FK → appointment_slots
  hashed_password VARCHAR                       patient_id UUID FK → users
  role ENUM(patient|clinic_staff|clinic_admin)  status ENUM(confirmed|cancelled|...)
  fcm_token VARCHAR (Firebase push token)
                                               appointment_slots
clinics                                          id UUID PK
  id UUID PK                                    clinic_id UUID FK → clinics
  name VARCHAR                                  provider_id UUID FK → providers
  location GEOGRAPHY(POINT,4326) ← PostGIS      start_time TIMESTAMPTZ
  ehr_system VARCHAR (epic|cerner|athena)        status ENUM(available|locked|booked|...)
  ehr_org_id VARCHAR (FHIR Organization.id)      ehr_slot_id VARCHAR (FHIR cross-ref)

providers
  id UUID PK
  clinic_id UUID FK → clinics
  full_name VARCHAR
  ehr_provider_id VARCHAR (FHIR Practitioner.id)
```

---

## Standby Mode (HIPAA-Safe Location Design)

| Design Choice | Rationale |
|---|---|
| One-shot location (not continuous) | Battery-friendly; avoids always-on GPS creepiness |
| User-declared availability window | Patient controls when they're "on standby" |
| Location stored in Redis (TTL) | Expires automatically; not persisted in HIPAA-covered DB |
| Push payload contains NO PHI | Only slot_id + generic message; details loaded post-auth |
| WebSocket JWT auth via query param | Avoids header limitations in WS protocol |

---

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| POST | /api/v1/auth/register | Patient registration |
| POST | /api/v1/auth/login | Login → JWT |
| POST | /api/v1/auth/fcm-token | Register Firebase push token |
| GET | /api/v1/slots/nearby | PostGIS radius search for available slots |
| POST | /api/v1/slots | Create slot (clinic staff) |
| PATCH | /api/v1/slots/{id}/status | Update slot status → triggers broadcast |
| POST | /api/v1/standby/activate | Go on standby (stores location in Redis) |
| POST | /api/v1/standby/deactivate | Go offline |
| POST | /api/v1/bookings/claim | Atomic slot claim (Redis NX lock) |
| POST | /api/v1/bookings/confirm | Confirm booking within 30s |
| GET | /api/v1/bookings/my | Patient booking history |
| POST | /api/v1/bookings/{id}/cancel | Cancel → re-broadcasts to standby |
| POST | /api/v1/webhooks/fhir | FHIR R4 Subscription webhook (EHR integration) |
| WS | /api/v1/ws?token= | Real-time slot event stream |

---

## Technology Rationale

| Choice | Why |
|---|---|
| FastAPI + asyncpg | Async throughout — handles WebSocket + HTTP concurrently without thread pool exhaustion |
| PostgreSQL + PostGIS | ST_DWithin radius queries in a single indexed SQL call; no external geo service needed |
| Redis SET NX | Atomic distributed lock primitive — the only correct way to prevent booking races at scale |
| Firebase FCM | Single SDK covers both iOS (APNs) and Android; batch send for simultaneous multi-patient broadcast |
| React Native + Expo | Single codebase for iOS + Android; Expo Notifications handles FCM/APNs registration |
| FHIR R4 Subscriptions | EHR-agnostic webhook standard; works with Epic, Cerner, and Athena without custom per-EHR polling |

---

## Next Steps for Production

1. **Celery + Redis Beat** — scheduled task to call `release_expired_lock()` every 30s
2. **Alembic migrations** — replace raw `init.sql` with versioned schema migrations
3. **Epic App Orchard** — submit for OAuth 2.0 SMART on FHIR credential approval
4. **SOC 2 Type II + HIPAA BAA** — required before any real clinic goes live
5. **Dynamic time-block splitting** — when a 45-min slot opens, offer it as 2× 20-min follow-ups
6. **Provider opt-in settings** — let doctors choose: "always fill my no-shows" vs. "ask me first"
