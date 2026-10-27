from auth import hash_password
from database import Base, SessionLocal, engine
from models import Department, Doctor, User, UserRole

Base.metadata.create_all(bind=engine)
db = SessionLocal()


def seed():
    admin = db.query(User).filter(User.username == "admin").first()
    if not admin:
        db.add(User(username="admin", password_hash=hash_password("admin123"), role=UserRole.admin, full_name="System Administrator"))

    dept = db.query(Department).filter(Department.name == "General Medicine").first()
    if not dept:
        dept = Department(name="General Medicine")
        db.add(dept)
        db.commit()
        db.refresh(dept)

    doctor_user = db.query(User).filter(User.username == "doctor1").first()
    if not doctor_user:
        doctor_user = User(username="doctor1", password_hash=hash_password("doctor123"), role=UserRole.doctor, full_name="Dr. Rahul Sharma")
        db.add(doctor_user)
        db.commit()
        db.refresh(doctor_user)
        db.add(Doctor(user_id=doctor_user.id, name="Dr. Rahul Sharma", department_id=dept.id, is_available=True))

    if not db.query(User).filter(User.username == "staff1").first():
        db.add(User(username="staff1", password_hash=hash_password("staff123"), role=UserRole.staff, full_name="Priya Patel"))

    db.commit()
    print("Admin  -> admin / admin123")
    print("Doctor -> doctor1 / doctor123")
    print("Staff  -> staff1 / staff123")


if __name__ == "__main__":
    try:
        seed()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()
