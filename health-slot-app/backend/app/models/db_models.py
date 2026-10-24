"""Tables: Clinic, Patient (standby), Appointment, Slot, Offer."""
from __future__ import annotations

from datetime import date, datetime

from sqlalchemy import Boolean, Date, DateTime, Float, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class Clinic(Base):
    __tablename__ = "clinics"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(120))
    lat: Mapped[float] = mapped_column(Float)
    lng: Mapped[float] = mapped_column(Float)
    specialty: Mapped[str] = mapped_column(String(40))
    # Comma-separated plan names, e.g. "BCBS,Tufts,MassHealth"
    accepted_insurance: Mapped[str] = mapped_column(String(400))

    def accepts(self, insurance: str) -> bool:
        return insurance in {s.strip() for s in self.accepted_insurance.split(",")}


class Patient(Base):
    """A standby patient: wants an earlier visit and opted in to last-minute offers."""

    __tablename__ = "patients"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(80))
    lat: Mapped[float] = mapped_column(Float)
    lng: Mapped[float] = mapped_column(Float)
    radius_miles: Mapped[float] = mapped_column(Float)
    insurance: Mapped[str] = mapped_column(String(60))
    specialty_needed: Mapped[str] = mapped_column(String(40))
    # 0-1: share of past last-minute claims they actually showed up for.
    reliability: Mapped[float] = mapped_column(Float, default=0.9)
    is_available: Mapped[bool] = mapped_column(Boolean, default=True)


class Appointment(Base):
    """An existing booking on today's schedule, with the features the model needs."""

    __tablename__ = "appointments"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    clinic_id: Mapped[int] = mapped_column(ForeignKey("clinics.id"))
    patient_label: Mapped[str] = mapped_column(String(80))
    start_time: Mapped[datetime] = mapped_column(DateTime)
    duration_min: Mapped[int] = mapped_column(Integer, default=30)

    # Model features (same meaning as the Kaggle columns)
    booked_at: Mapped[datetime] = mapped_column(DateTime)
    age: Mapped[int] = mapped_column(Integer)
    gender: Mapped[str] = mapped_column(String(1))
    scholarship: Mapped[int] = mapped_column(Integer, default=0)
    hypertension: Mapped[int] = mapped_column(Integer, default=0)
    diabetes: Mapped[int] = mapped_column(Integer, default=0)
    alcoholism: Mapped[int] = mapped_column(Integer, default=0)
    handcap: Mapped[int] = mapped_column(Integer, default=0)
    sms_received: Mapped[int] = mapped_column(Integer, default=0)
    prior_appts: Mapped[int] = mapped_column(Integer, default=0)
    prior_noshows: Mapped[int] = mapped_column(Integer, default=0)

    risk: Mapped[float] = mapped_column(Float, default=0.0)
    # scheduled | no_show | cancelled | unconfirmed
    status: Mapped[str] = mapped_column(String(20), default="scheduled")

    clinic: Mapped[Clinic] = relationship()
    slot: Mapped["Slot | None"] = relationship(back_populates="appointment", uselist=False)

    @property
    def appt_date(self) -> date:
        return self.start_time.date()


class Slot(Base):
    """A freed-up time that we're trying to refill."""

    __tablename__ = "slots"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    appointment_id: Mapped[int] = mapped_column(ForeignKey("appointments.id"), unique=True)
    clinic_id: Mapped[int] = mapped_column(ForeignKey("clinics.id"))
    start_time: Mapped[datetime] = mapped_column(DateTime)
    reason: Mapped[str] = mapped_column(String(20))
    # open | booked | expired
    status: Mapped[str] = mapped_column(String(20), default="open")
    round: Mapped[int] = mapped_column(Integer, default=0)
    radius_multiplier: Mapped[float] = mapped_column(Float, default=1.0)
    opened_at: Mapped[datetime] = mapped_column(DateTime)
    expires_at: Mapped[datetime] = mapped_column(DateTime)
    booked_patient_id: Mapped[int | None] = mapped_column(ForeignKey("patients.id"), nullable=True)
    booked_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    appointment: Mapped[Appointment] = relationship(back_populates="slot")
    clinic: Mapped[Clinic] = relationship()
    booked_patient: Mapped[Patient | None] = relationship()
    offers: Mapped[list["Offer"]] = relationship(back_populates="slot", order_by="Offer.rank")


class Offer(Base):
    """Record that a slot was offered to a patient (needed to authorise a claim)."""

    __tablename__ = "offers"
    __table_args__ = (UniqueConstraint("slot_id", "patient_id"),)
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    slot_id: Mapped[int] = mapped_column(ForeignKey("slots.id"))
    patient_id: Mapped[int] = mapped_column(ForeignKey("patients.id"))
    round: Mapped[int] = mapped_column(Integer)
    rank: Mapped[int] = mapped_column(Integer)
    distance_miles: Mapped[float] = mapped_column(Float)
    sent_at: Mapped[datetime] = mapped_column(DateTime)

    slot: Mapped[Slot] = relationship(back_populates="offers")
    patient: Mapped[Patient] = relationship()
