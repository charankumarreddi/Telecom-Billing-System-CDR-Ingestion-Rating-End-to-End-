from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field


class CDRIn(BaseModel):
	msisdn: str = Field(..., description="Subscriber MSISDN")
	call_type: str = Field(..., description="voice|sms|data")
	duration_secs: int = 0
	bytes_used: int = 0
	occurred_at: Optional[datetime] = None


class CDROut(BaseModel):
	id: int
	msisdn: str
	call_type: str
	duration_secs: int
	bytes_used: int
	occurred_at: datetime

	class Config:
		from_attributes = True


class RatedEventOut(BaseModel):
	id: int
	cdr_id: int
	msisdn: str
	call_type: str
	charge_amount: float
	currency: str
	rated_at: datetime

	class Config:
		from_attributes = True


class IngestResponse(BaseModel):
	cdr: CDROut
	rated: RatedEventOut


class UsageItem(BaseModel):
	call_type: str
	total_events: int
	total_duration_secs: int
	total_bytes: int
	total_charge: float


class UsageSummary(BaseModel):
	msisdn: str
	from_ts: datetime
	to_ts: datetime
	items: List[UsageItem]
	total_charge: float

