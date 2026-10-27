import enum

from sqlalchemy import Boolean, Column, DateTime, Enum, ForeignKey, Integer, String
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from database import Base


class UserRole(str, enum.Enum):
    admin = "admin"
    doctor = "doctor"
    staff = "staff"


class Priority(str, enum.Enum):
    Emergency = "Emergency"
    Normal = "Normal"


class QueueStatus(str, enum.Enum):
    Waiting = "Waiting"
    InProgress = "In Progress"
    Done = "Done"
    NoShow = "No Show"


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    role = Column(Enum(UserRole), nullable=False)
    full_name = Column(String(100), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    doctor_profile = relationship("Doctor", back_populates="user", uselist=False)
    registered_patients = relationship("Patient", back_populates="registered_by_user")


class Department(Base):
    __tablename__ = "departments"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), unique=True, nullable=False)

    doctors = relationship("Doctor", back_populates="department")


class Doctor(Base):
    __tablename__ = "doctors"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True, nullable=False)
    name = Column(String(100), nullable=False)
    department_id = Column(Integer, ForeignKey("departments.id"), nullable=False)
    is_available = Column(Boolean, default=True)

    user = relationship("User", back_populates="doctor_profile")
    department = relationship("Department", back_populates="doctors")
    queue_entries = relationship("QueueEntry", back_populates="doctor")


class Patient(Base):
    __tablename__ = "patients"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    age = Column(Integer, nullable=False)
    gender = Column(String(20), nullable=False)
    contact = Column(String(20), nullable=True)
    registered_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    registered_by_user = relationship("User", back_populates="registered_patients")
    queue_entries = relationship("QueueEntry", back_populates="patient")


class QueueEntry(Base):
    __tablename__ = "queue_entries"

    id = Column(Integer, primary_key=True, index=True)
    token_no = Column(String(30), unique=True, nullable=False, index=True)
    patient_id = Column(Integer, ForeignKey("patients.id"), nullable=False)
    doctor_id = Column(Integer, ForeignKey("doctors.id"), nullable=False)
    priority = Column(Enum(Priority), nullable=False, default=Priority.Normal)
    status = Column(Enum(QueueStatus), nullable=False, default=QueueStatus.Waiting)
    check_in_time = Column(DateTime(timezone=True), server_default=func.now())
    called_time = Column(DateTime(timezone=True), nullable=True)
    completed_time = Column(DateTime(timezone=True), nullable=True)

    patient = relationship("Patient", back_populates="queue_entries")
    doctor = relationship("Doctor", back_populates="queue_entries")
