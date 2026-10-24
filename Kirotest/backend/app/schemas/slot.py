from uuid import UUID
from datetime import datetime
from pydantic import BaseModel, Field, model_validator


class SlotRead(BaseModel):
    id: UUID
    clinic_id: UUID
    provider_id: UUID
    start_time: datetime
    end_time: datetime
    duration_minutes: int
    appointment_type: str
    status: str
    provider_name: str | None = None   # populated via join in service layer
    clinic_name: str | None = None
    distance_meters: float | None = None  # injected by geospatial query

    model_config = {"from_attributes": True}


class SlotCreate(BaseModel):
    clinic_id: UUID
    provider_id: UUID
    start_time: datetime
    end_time: datetime
    appointment_type: str = "follow_up"

    @model_validator(mode="after")
    def validate_times(self) -> "SlotCreate":
        if self.end_time <= self.start_time:
            raise ValueError("end_time must be after start_time")
        return self


class SlotStatusUpdate(BaseModel):
    status: str  # validated at service layer against allowed transitions


class StandbyActivate(BaseModel):
    lat: float = Field(ge=-90, le=90)
    lng: float = Field(ge=-180, le=180)
    radius_meters: int = Field(default=5000, ge=500, le=25_000)
    duration_seconds: int = Field(default=7200, ge=300, le=28_800)  # max 8 hours


class BookingClaim(BaseModel):
    slot_id: UUID
    notes: str | None = None
