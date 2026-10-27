from pathlib import Path

from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy import or_
from sqlalchemy.orm import Session, joinedload

from auth import role_required
from database import get_db
from models import Doctor, Patient, QueueEntry, User

router = APIRouter(prefix="/doctor", tags=["Doctor"])
templates = Jinja2Templates(directory=str(Path(__file__).resolve().parents[1] / "templates"))


def _doctor(db: Session, user: User) -> Doctor | None:
    return db.query(Doctor).filter(Doctor.user_id == user.id).first()


@router.get("/queue", response_class=HTMLResponse)
def doctor_queue(
    request: Request,
    current_user: User = Depends(role_required("doctor")),
    db: Session = Depends(get_db),
):
    doctor = _doctor(db, current_user)
    return templates.TemplateResponse(
        "doctor_queue.html",
        {"request": request, "user": current_user, "doctor_id": doctor.id if doctor else ""},
    )


@router.get("/history", response_class=HTMLResponse)
def patient_history(
    request: Request,
    current_user: User = Depends(role_required("doctor")),
    db: Session = Depends(get_db),
):
    doctor = _doctor(db, current_user)
    query = (request.query_params.get("q") or "").strip()
    visits = []
    if doctor and query:
        like = f"%{query}%"
        visits = (
            db.query(QueueEntry)
            .join(Patient)
            .options(joinedload(QueueEntry.patient))
            .filter(
                QueueEntry.doctor_id == doctor.id,
                or_(Patient.name.ilike(like), Patient.contact.ilike(like), QueueEntry.token_no.ilike(like)),
            )
            .order_by(QueueEntry.check_in_time.desc())
            .limit(50)
            .all()
        )
    return templates.TemplateResponse(
        "history.html",
        {"request": request, "user": current_user, "query": query, "visits": visits},
    )
