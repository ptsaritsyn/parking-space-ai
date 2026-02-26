from datetime import datetime, timezone
from pydantic import BaseModel, Field, field_validator, model_validator


class StaticParkingInfo(BaseModel):
    content: str = Field(..., min_length=10, max_length=1024)


class ReservationRequest(BaseModel):
    name: str = Field(min_length=2, max_length=50)
    surname: str = Field(min_length=2, max_length=50)
    car_number: str = Field(pattern=r"^[A-Z]{2}\d{4}[A-Z]{2}$")
    reservation_from: datetime
    reservation_to: datetime

    @field_validator("reservation_from", "reservation_to")
    @classmethod
    def check_not_past(cls, v):
        now = datetime.now(timezone.utc) if v.tzinfo else datetime.now()
        if v < now:
            raise ValueError("Reservation dates must not be in the past")
        return v

    @model_validator(mode="after")
    def check_dates(self):
        if self.reservation_to <= self.reservation_from:
            raise ValueError("reservation_to must be after reservation_from")
        return self
