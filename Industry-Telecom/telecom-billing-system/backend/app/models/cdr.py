from datetime import datetime
from enum import Enum
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Float
from sqlalchemy.orm import relationship, Mapped, mapped_column

from ..database import Base


class CallType(str, Enum):
    voice = "voice"
    sms = "sms"
    data = "data"


class Subscriber(Base):
    __tablename__ = "subscribers"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    msisdn: Mapped[str] = mapped_column(String(20), unique=True, index=True, nullable=False)
    plan_id: Mapped[int] = mapped_column(ForeignKey("tariff_plans.id"), nullable=False)

    plan: Mapped["TariffPlan"] = relationship("TariffPlan", back_populates="subscribers")


class TariffPlan(Base):
    __tablename__ = "tariff_plans"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    voice_rate_per_min: Mapped[float] = mapped_column(Float, default=0.5)
    sms_rate: Mapped[float] = mapped_column(Float, default=0.1)
    data_rate_per_mb: Mapped[float] = mapped_column(Float, default=0.05)

    subscribers: Mapped[list[Subscriber]] = relationship("Subscriber", back_populates="plan")


class CDR(Base):
    __tablename__ = "cdrs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    msisdn: Mapped[str] = mapped_column(String(20), index=True, nullable=False)
    call_type: Mapped[str] = mapped_column(String(10), nullable=False)
    duration_secs: Mapped[int] = mapped_column(Integer, default=0)  # for voice
    bytes_used: Mapped[int] = mapped_column(Integer, default=0)     # for data
    occurred_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, index=True)

    rated_event: Mapped["RatedEvent"] = relationship("RatedEvent", uselist=False, back_populates="cdr")


class RatedEvent(Base):
    __tablename__ = "rated_events"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    cdr_id: Mapped[int] = mapped_column(ForeignKey("cdrs.id"), unique=True, nullable=False)
    msisdn: Mapped[str] = mapped_column(String(20), index=True, nullable=False)
    call_type: Mapped[str] = mapped_column(String(10), nullable=False)
    charge_amount: Mapped[float] = mapped_column(Float, nullable=False)
    currency: Mapped[str] = mapped_column(String(3), default="USD")
    rated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    cdr: Mapped[CDR] = relationship("CDR", back_populates="rated_event")
