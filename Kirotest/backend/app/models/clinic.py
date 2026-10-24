"""
Clinic model — stores location as a PostGIS POINT for geospatial queries.
"""
import uuid
from datetime import datetime

from geoalchemy2 import Geometry
from sqlalchemy import DateTime, String, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class Clinic(Base):
    __tablename__ = "clinics"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    address: Mapped[str] = mapped_column(String(512), nullable=False)
    phone: Mapped[str | None] = mapped_column(String(20))
    specialty: Mapped[str | None] = mapped_column(String(100))  # e.g. "primary_care"

    # PostGIS point: SRID 4326 = standard WGS-84 lat/lng
    location: Mapped[Geometry] = mapped_column(
        Geometry(geometry_type="POINT", srid=4326), nullable=False
    )

    # EHR integration identifiers
    ehr_system: Mapped[str | None] = mapped_column(String(50))   # "epic" | "cerner" | "athena"
    ehr_org_id: Mapped[str | None] = mapped_column(String(255))  # FHIR Organization.id

    description: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    # Relationships
    providers: Mapped[list["Provider"]] = relationship(back_populates="clinic")  # noqa: F821
    slots: Mapped[list["AppointmentSlot"]] = relationship(back_populates="clinic")  # noqa: F821
