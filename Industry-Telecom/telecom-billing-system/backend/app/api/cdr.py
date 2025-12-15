from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import CDR
from ..schemas import CDRIn, CDROut, IngestResponse, RatedEventOut
from ..services.rating_service import rate_cdr

router = APIRouter()


@router.post("/ingest", response_model=IngestResponse)
def ingest_cdr(payload: CDRIn, db: Session = Depends(get_db)):
    occurred = payload.occurred_at or datetime.utcnow()
    cdr = CDR(
        msisdn=payload.msisdn,
        call_type=payload.call_type.lower(),
        duration_secs=payload.duration_secs,
        bytes_used=payload.bytes_used,
        occurred_at=occurred,
    )
    db.add(cdr)
    db.commit()
    db.refresh(cdr)

    rated = rate_cdr(db, cdr)

    return IngestResponse(cdr=CDROut.model_validate(cdr), rated=RatedEventOut.model_validate(rated))


@router.get("/{cdr_id}", response_model=IngestResponse)
def get_cdr(cdr_id: int, db: Session = Depends(get_db)):
    cdr = db.query(CDR).filter_by(id=cdr_id).first()
    if not cdr:
        raise HTTPException(status_code=404, detail="CDR not found")
    rated = cdr.rated_event
    if not rated:
        # In case rating failed earlier
        rated = rate_cdr(db, cdr)
    return IngestResponse(cdr=CDROut.model_validate(cdr), rated=RatedEventOut.model_validate(rated))
