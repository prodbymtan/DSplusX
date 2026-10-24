"""
AppointmentSlot — the core entity.

Status lifecycle:
  available ──► locked (patient claiming, 30-second hold)
  locked    ──► booked  (patient confirmed)
  locked    ──► available (lock expired, nobody confirmed)
  booked    ──► no_show  (patient never arrived, triggered after threshold)
  booked    ──► completed
  available ──► cancelled (provider cancelled in advance)
"""
import uuid
from datetime import datetime

from sqlalchemy import DateTime, Enum, ForeignKey, Integer, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class SlotStatus(str):
    AVAILABLE = "available"
    LOCKED = "locked"
    BOOKED = "booked"
    NO_SHOW = "no_show"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class AppointmentType(str):
    NEW_PATIENT = "new_patient"
    FOLLOW_UP = "follow_up"
    URGENT = "urgent"
    TELEHEALTH = "telehealth"


class AppointmentSlot(Base):
    __tablename__ = "appointment_slots"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    clinic_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("clinics.id", ondelete="CASCADE"), nullable=False
    )
    provider_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("providers.id", ondelete="CASCADE"), nullable=False
    )

    # Time
    start_time: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)
    end_time: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    duration_minutes: Mapped[int] = mapped_column(Integer, nullable=False)

    appointment_type: Mapped[str] = mapped_column(
        Enum("new_patient", "follow_up", "urgent", "telehealth", name="appointment_type"),
        nullable=False,
        default="follow_up",
    )

    status: Mapped[str] = mapped_column(
        Enum(
            "available", "locked", "booked", "no_show", "completed", "cancelled",
            name="slot_status",
        ),
        nullable=False,
        default="available",
        index=True,
    )

    # EHR cross-reference
    ehr_slot_id: Mapped[str | None] = mapped_column(String(255))

    # Audit
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    # Relationships
    clinic: Mapped["Clinic"] = relationship(back_populates="slots")  # noqa: F821
    provider: Mapped["Provider"] = relationship(back_populates="slots")  # noqa: F821
    booking: Mapped["Booking | None"] = relationship(back_populates="slot", uselist=False)  # noqa: F821
