from datetime import datetime
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from ..database import get_db
from ..schemas import UsageSummary, UsageItem
from ..services.rating_service import aggregate_usage

router = APIRouter()


@router.get("/{msisdn}/usage", response_model=UsageSummary)
def get_usage(
    msisdn: str,
    from_ts: datetime = Query(..., description="Start timestamp in ISO format"),
    to_ts: datetime = Query(..., description="End timestamp in ISO format"),
    db: Session = Depends(get_db),
):
    items, total = aggregate_usage(db, msisdn, from_ts, to_ts)
    return UsageSummary(
        msisdn=msisdn,
        from_ts=from_ts,
        to_ts=to_ts,
        items=[UsageItem(**it) for it in items],
        total_charge=total,
    )
