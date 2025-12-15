from datetime import datetime
from typing import Optional
from sqlalchemy.orm import Session

from ..models import Subscriber, TariffPlan, CDR, RatedEvent


DEFAULT_CURRENCY = "USD"


def ensure_seed_data(db: Session):
    """Seed one default plan and one demo subscriber if none exist."""
    if not db.query(TariffPlan).first():
        plan = TariffPlan(
            name="Basic",
            voice_rate_per_min=0.5,
            sms_rate=0.1,
            data_rate_per_mb=0.05,
        )
        db.add(plan)
        db.flush()
        sub = Subscriber(msisdn="9999999999", plan_id=plan.id)
        db.add(sub)
        db.commit()


def get_or_create_subscriber(db: Session, msisdn: str) -> Subscriber:
    sub = db.query(Subscriber).filter_by(msisdn=msisdn).first()
    if sub:
        return sub
    # attach to first plan
    plan = db.query(TariffPlan).first()
    if not plan:
        ensure_seed_data(db)
        plan = db.query(TariffPlan).first()
    sub = Subscriber(msisdn=msisdn, plan_id=plan.id)
    db.add(sub)
    db.commit()
    db.refresh(sub)
    return sub


def rate_cdr(db: Session, cdr: CDR) -> RatedEvent:
    sub = get_or_create_subscriber(db, cdr.msisdn)
    plan = sub.plan

    charge = 0.0
    ct = cdr.call_type.lower()
    if ct == "voice":
        mins = (cdr.duration_secs + 59) // 60
        charge = mins * plan.voice_rate_per_min
    elif ct == "sms":
        charge = plan.sms_rate
    elif ct == "data":
        mb = cdr.bytes_used / (1024 * 1024)
        charge = mb * plan.data_rate_per_mb
    else:
        raise ValueError(f"Unknown call_type: {cdr.call_type}")

    rated = RatedEvent(
        cdr_id=cdr.id,
        msisdn=cdr.msisdn,
        call_type=cdr.call_type,
        charge_amount=round(charge, 4),
        currency=DEFAULT_CURRENCY,
        rated_at=datetime.utcnow(),
    )
    db.add(rated)
    db.commit()
    db.refresh(rated)
    return rated


def aggregate_usage(db: Session, msisdn: str, from_ts: datetime, to_ts: datetime):
    from sqlalchemy import func

    rows = (
        db.query(
            CDR.call_type.label("call_type"),
            func.count(CDR.id).label("total_events"),
            func.sum(CDR.duration_secs).label("total_duration_secs"),
            func.sum(CDR.bytes_used).label("total_bytes"),
            func.sum(RatedEvent.charge_amount).label("total_charge"),
        )
        .join(RatedEvent, RatedEvent.cdr_id == CDR.id)
        .filter(CDR.msisdn == msisdn)
        .filter(CDR.occurred_at >= from_ts, CDR.occurred_at <= to_ts)
        .group_by(CDR.call_type)
        .all()
    )

    items = []
    total = 0.0
    for r in rows:
        total += float(r.total_charge or 0)
        items.append(
            dict(
                call_type=r.call_type,
                total_events=int(r.total_events or 0),
                total_duration_secs=int(r.total_duration_secs or 0),
                total_bytes=int(r.total_bytes or 0),
                total_charge=float(r.total_charge or 0.0),
            )
        )
    return items, total
