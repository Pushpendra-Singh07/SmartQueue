from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import case
from sqlalchemy.orm import Session, joinedload

from auth import login_required
from database import get_db
from models import Doctor, Priority, QueueEntry, QueueStatus, User
from schemas import QueueEntryOut

router = APIRouter(prefix="/api/queue", tags=["Queue API"])


def _queue(db: Session, doctor_id: int):
    return (
        db.query(QueueEntry)
        .options(joinedload(QueueEntry.patient))
        .filter(
            QueueEntry.doctor_id == doctor_id,
            QueueEntry.status.in_([QueueStatus.Waiting, QueueStatus.InProgress]),
        )
        .order_by(
            case((QueueEntry.priority == Priority.Emergency, 0), else_=1),
            QueueEntry.check_in_time.asc(),
        )
        .all()
    )


def _doctor_for(db: Session, user: User) -> Doctor:
    if user.role.value != "doctor":
        raise HTTPException(status_code=403, detail="Doctors only")
    doctor = db.query(Doctor).filter(Doctor.user_id == user.id).first()
    if not doctor:
        raise HTTPException(status_code=404, detail="Doctor profile missing")
    return doctor


@router.get("/doctor/{doctor_id}", response_model=list[QueueEntryOut])
def get_doctor_queue(doctor_id: int, current_user: User = Depends(login_required), db: Session = Depends(get_db)):
    if current_user.role.value == "doctor":
        doctor = _doctor_for(db, current_user)
        if doctor.id != doctor_id:
            raise HTTPException(status_code=403, detail="Not your queue")
    return _queue(db, doctor_id)


@router.post("/call-next/{doctor_id}")
def call_next(doctor_id: int, current_user: User = Depends(login_required), db: Session = Depends(get_db)):
    doctor = _doctor_for(db, current_user)
    if doctor.id != doctor_id:
        raise HTTPException(status_code=403, detail="Not your queue")
    waiting = next((entry for entry in _queue(db, doctor_id) if entry.status == QueueStatus.Waiting), None)
    if not waiting:
        raise HTTPException(status_code=404, detail="No waiting patients")
    waiting.status = QueueStatus.InProgress
    waiting.called_time = datetime.now()
    db.commit()
    return {"ok": True, "token_no": waiting.token_no}


def _own_entry(db: Session, user: User, entry_id: int) -> QueueEntry:
    doctor = _doctor_for(db, user)
    entry = db.query(QueueEntry).filter(QueueEntry.id == entry_id, QueueEntry.doctor_id == doctor.id).first()
    if not entry:
        raise HTTPException(status_code=404, detail="Queue entry not found")
    return entry


@router.post("/complete/{entry_id}")
def complete_entry(entry_id: int, current_user: User = Depends(login_required), db: Session = Depends(get_db)):
    entry = _own_entry(db, current_user, entry_id)
    entry.status = QueueStatus.Done
    entry.completed_time = datetime.now()
    if not entry.called_time:
        entry.called_time = entry.completed_time
    db.commit()
    return {"ok": True}


@router.post("/no-show/{entry_id}")
def no_show_entry(entry_id: int, current_user: User = Depends(login_required), db: Session = Depends(get_db)):
    entry = _own_entry(db, current_user, entry_id)
    entry.status = QueueStatus.NoShow
    entry.completed_time = datetime.now()
    db.commit()
    return {"ok": True}
