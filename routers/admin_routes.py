from datetime import datetime, timedelta
from pathlib import Path

from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy import func
from sqlalchemy.orm import Session, joinedload

from auth import hash_password, role_required
from database import get_db
from models import Department, Doctor, QueueEntry, QueueStatus, User, UserRole

router = APIRouter(prefix="/admin", tags=["Admin"])
templates = Jinja2Templates(directory=str(Path(__file__).resolve().parents[1] / "templates"))


def _minutes(start, end):
    if not start or not end:
        return None
    start = start.replace(tzinfo=None)
    end = end.replace(tzinfo=None)
    return max((end - start).total_seconds() / 60.0, 0)


@router.get("/dashboard", response_class=HTMLResponse)
def dashboard(
    request: Request,
    current_user: User = Depends(role_required("admin")),
    db: Session = Depends(get_db),
):
    today = datetime.now().date()
    days = [(today - timedelta(days=offset)) for offset in range(13, -1, -1)]
    day_labels = [day.strftime("%d %b") for day in days]

    entries = db.query(QueueEntry).options(joinedload(QueueEntry.doctor).joinedload(Doctor.department)).all()

    per_day = {day.isoformat(): 0 for day in days}
    dept_counts: dict[str, int] = {}
    doctor_counts: dict[str, int] = {}
    waits = []
    done = no_show = 0

    for entry in entries:
        if entry.check_in_time:
            key = entry.check_in_time.replace(tzinfo=None).date().isoformat()
            if key in per_day:
                per_day[key] += 1
        dept_name = entry.doctor.department.name if entry.doctor and entry.doctor.department else "Unknown"
        doctor_name = entry.doctor.name if entry.doctor else "Unknown"
        dept_counts[dept_name] = dept_counts.get(dept_name, 0) + 1
        doctor_counts[doctor_name] = doctor_counts.get(doctor_name, 0) + 1
        if entry.status == QueueStatus.Done:
            done += 1
            minutes = _minutes(entry.check_in_time, entry.called_time)
            if minutes is not None:
                waits.append(minutes)
        elif entry.status == QueueStatus.NoShow:
            no_show += 1

    finished = done + no_show
    chart = {
        "days": day_labels,
        "patients": [per_day[day.isoformat()] for day in days],
        "departments": list(dept_counts.keys()) or ["None"],
        "departmentCounts": list(dept_counts.values()) or [0],
        "doctors": list(doctor_counts.keys()) or ["None"],
        "doctorCounts": list(doctor_counts.values()) or [0],
    }
    stats = {
        "total": len(entries),
        "today": per_day[today.isoformat()],
        "avg_wait": round(sum(waits) / len(waits), 1) if waits else 0,
        "no_show_rate": round((no_show / finished) * 100, 1) if finished else 0,
        "done": done,
        "no_show": no_show,
    }
    return templates.TemplateResponse(
        "dashboard.html",
        {"request": request, "user": current_user, "stats": stats, "chart": chart},
    )


@router.get("/doctors", response_class=HTMLResponse)
def doctors_page(
    request: Request,
    current_user: User = Depends(role_required("admin")),
    db: Session = Depends(get_db),
):
    doctors = db.query(Doctor).options(joinedload(Doctor.department), joinedload(Doctor.user)).all()
    departments = db.query(Department).order_by(Department.name).all()
    return templates.TemplateResponse(
        "doctors.html",
        {
            "request": request,
            "user": current_user,
            "doctors": doctors,
            "departments": departments,
            "error": request.query_params.get("error"),
        },
    )


@router.post("/doctors")
def create_doctor(
    request: Request,
    full_name: str = Form(...),
    username: str = Form(...),
    password: str = Form(...),
    department_id: int = Form(...),
    current_user: User = Depends(role_required("admin")),
    db: Session = Depends(get_db),
):
    if db.query(User).filter(User.username == username.strip()).first():
        return RedirectResponse("/admin/doctors?error=Username+already+exists", status_code=303)
    if not db.query(Department).filter(Department.id == department_id).first():
        return RedirectResponse("/admin/doctors?error=Pick+a+department+first", status_code=303)
    user = User(
        username=username.strip(),
        password_hash=hash_password(password),
        role=UserRole.doctor,
        full_name=full_name.strip(),
    )
    db.add(user)
    db.flush()
    db.add(Doctor(user_id=user.id, name=full_name.strip(), department_id=department_id, is_available=True))
    db.commit()
    return RedirectResponse("/admin/doctors", status_code=303)


@router.post("/doctors/{doctor_id}/availability")
def toggle_doctor(
    doctor_id: int,
    current_user: User = Depends(role_required("admin")),
    db: Session = Depends(get_db),
):
    doctor = db.query(Doctor).filter(Doctor.id == doctor_id).first()
    if doctor:
        doctor.is_available = not doctor.is_available
        db.commit()
    return RedirectResponse("/admin/doctors", status_code=303)


@router.get("/staff", response_class=HTMLResponse)
def staff_page(
    request: Request,
    current_user: User = Depends(role_required("admin")),
    db: Session = Depends(get_db),
):
    staff = db.query(User).filter(User.role == UserRole.staff).order_by(User.full_name).all()
    return templates.TemplateResponse(
        "staff.html",
        {"request": request, "user": current_user, "staff": staff, "error": request.query_params.get("error")},
    )


@router.post("/staff")
def create_staff(
    full_name: str = Form(...),
    username: str = Form(...),
    password: str = Form(...),
    current_user: User = Depends(role_required("admin")),
    db: Session = Depends(get_db),
):
    if db.query(User).filter(User.username == username.strip()).first():
        return RedirectResponse("/admin/staff?error=Username+already+exists", status_code=303)
    db.add(
        User(
            username=username.strip(),
            password_hash=hash_password(password),
            role=UserRole.staff,
            full_name=full_name.strip(),
        )
    )
    db.commit()
    return RedirectResponse("/admin/staff", status_code=303)


@router.get("/departments", response_class=HTMLResponse)
def departments_page(
    request: Request,
    current_user: User = Depends(role_required("admin")),
    db: Session = Depends(get_db),
):
    departments = db.query(Department).order_by(Department.name).all()
    counts = dict(
        db.query(Doctor.department_id, func.count(Doctor.id)).group_by(Doctor.department_id).all()
    )
    return templates.TemplateResponse(
        "departments.html",
        {
            "request": request,
            "user": current_user,
            "departments": departments,
            "counts": counts,
            "error": request.query_params.get("error"),
        },
    )


@router.post("/departments")
def create_department(
    name: str = Form(...),
    current_user: User = Depends(role_required("admin")),
    db: Session = Depends(get_db),
):
    clean = name.strip()
    if db.query(Department).filter(Department.name == clean).first():
        return RedirectResponse("/admin/departments?error=Department+already+exists", status_code=303)
    db.add(Department(name=clean))
    db.commit()
    return RedirectResponse("/admin/departments", status_code=303)
