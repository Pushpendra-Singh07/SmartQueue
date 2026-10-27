from datetime import datetime
from pathlib import Path

from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session, joinedload

from auth import role_required
from database import get_db
from models import Doctor, Patient, Priority, QueueEntry, QueueStatus, User

router = APIRouter(prefix="/staff", tags=["Staff"])
templates = Jinja2Templates(directory=str(Path(__file__).resolve().parents[1] / "templates"))


def _token_no(db: Session) -> str:
    today = datetime.now().strftime("%Y%m%d")
    count = db.query(QueueEntry).filter(QueueEntry.token_no.like(f"T{today}%")).count() + 1
    return f"T{today}-{count:03d}"


@router.get("/register", response_class=HTMLResponse)
def register_page(
    request: Request,
    current_user: User = Depends(role_required("staff")),
    db: Session = Depends(get_db),
):
    doctors = (
        db.query(Doctor)
        .options(joinedload(Doctor.department))
        .filter(Doctor.is_available.is_(True))
        .all()
    )
    recent = (
        db.query(QueueEntry)
        .options(joinedload(QueueEntry.patient), joinedload(QueueEntry.doctor))
        .order_by(QueueEntry.id.desc())
        .limit(8)
        .all()
    )
    return templates.TemplateResponse(
        "register.html",
        {"request": request, "user": current_user, "doctors": doctors, "recent": recent, "token": None, "error": None},
    )


@router.post("/register", response_class=HTMLResponse)
def register_patient(
    request: Request,
    name: str = Form(...),
    age: int = Form(...),
    gender: str = Form(...),
    contact: str = Form(""),
    doctor_id: int = Form(...),
    priority: str = Form("Normal"),
    current_user: User = Depends(role_required("staff")),
    db: Session = Depends(get_db),
):
    doctors = (
        db.query(Doctor)
        .options(joinedload(Doctor.department))
        .filter(Doctor.is_available.is_(True))
        .all()
    )
    doctor = db.query(Doctor).filter(Doctor.id == doctor_id, Doctor.is_available.is_(True)).first()
    if not doctor:
        return templates.TemplateResponse(
            "register.html",
            {"request": request, "user": current_user, "doctors": doctors, "recent": [], "token": None, "error": "Select an available doctor"},
            status_code=400,
        )
    patient = Patient(
        name=name.strip(),
        age=age,
        gender=gender,
        contact=contact.strip() or None,
        registered_by=current_user.id,
    )
    db.add(patient)
    db.flush()
    entry = QueueEntry(
        token_no=_token_no(db),
        patient_id=patient.id,
        doctor_id=doctor.id,
        priority=Priority(priority),
        status=QueueStatus.Waiting,
    )
    db.add(entry)
    db.commit()
    recent = (
        db.query(QueueEntry)
        .options(joinedload(QueueEntry.patient), joinedload(QueueEntry.doctor))
        .order_by(QueueEntry.id.desc())
        .limit(8)
        .all()
    )
    return templates.TemplateResponse(
        "register.html",
        {"request": request, "user": current_user, "doctors": doctors, "recent": recent, "token": entry.token_no, "error": None},
    )


@router.get("/queue", response_class=HTMLResponse)
def staff_queue(
    request: Request,
    current_user: User = Depends(role_required("staff")),
    db: Session = Depends(get_db),
):
    doctors = db.query(Doctor).options(joinedload(Doctor.department)).all()
    return templates.TemplateResponse(
        "queue.html",
        {"request": request, "user": current_user, "doctors": doctors},
    )
