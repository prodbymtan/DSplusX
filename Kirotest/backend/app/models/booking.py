"""
Booking — created when a patient successfully claims a slot.
"""
import uuid
from datetime import datetime

from sqlalchemy import DateTime, Enum, ForeignKey, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class Booking(Base):
    __tablename__ = "bookings"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    slot_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("appointment_slots.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,   # one booking per slot
    )
    patient_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )

    status: Mapped[str] = mapped_column(
        Enum(
            "confirmed", "cancelled_by_patient", "cancelled_by_clinic",
            "attended", "no_show",
            name="booking_status",
        ),
        nullable=False,
        default="confirmed",
    )

    notes: Mapped[str | None] = mapped_column(Text)  # patient-supplied reason / notes

    confirmed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    # Relationships
    slot: Mapped["AppointmentSlot"] = relationship(back_populates="booking")  # noqa: F821
    patient: Mapped["User"] = relationship(back_populates="bookings")  # noqa: F821
