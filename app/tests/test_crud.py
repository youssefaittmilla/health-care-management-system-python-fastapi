import pytest
from datetime import datetime, timedelta, time
from sqlalchemy.orm import Session

from app.crud.crud_patient import patient
from app.crud.crud_doctor import doctor
from app.crud.crud_appointment import appointment
from app.crud.crud_user import user

from app.schemas.patient import PatientCreate
from app.schemas.doctor import DoctorCreate, AvailabilityCreate
from app.schemas.appointment import AppointmentCreate, AppointmentStatus
from app.schemas.user import UserCreate, UserRole

# Import DB de test depuis test_api
from app.tests.test_api import TestingSessionLocal

@pytest.fixture
def db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()

# ------------------- PATIENT -------------------
def test_create_patient(db: Session):
    patient_in = PatientCreate(
        first_name="Test",
        last_name="Patient",
        date_of_birth=datetime(1990, 1, 1).date(),
        email="test.patient@example.com",
        phone="1234567890",
        address="123 Test St",
        insurance_provider="Test Insurance",
        insurance_id="TI123456"
    )
    patient_obj = patient.create(db, obj_in=patient_in)
    assert patient_obj.id is not None
    assert patient_obj.first_name == patient_in.first_name
    assert patient_obj.email == patient_in.email

# ------------------- DOCTOR -------------------
def test_create_doctor(db: Session):
    doctor_in = DoctorCreate(
        first_name="Test",
        last_name="Doctor",
        email="test.doctor@example.com",
        phone="0987654321",
        specialization="Test Specialty"
    )
    doctor_obj = doctor.create(db, obj_in=doctor_in)
    assert doctor_obj.id is not None
    assert doctor_obj.specialization == doctor_in.specialization

def test_doctor_availability(db: Session):
    doctor_in = DoctorCreate(
        first_name="Availability",
        last_name="Test",
        email="availability.test@example.com",
        phone="1122334455",
        specialization="Test Specialty"
    )
    doctor_obj = doctor.create(db, obj_in=doctor_in)
    availability_in = AvailabilityCreate(
        day_of_week=1,
        start_time=time(9, 0),
        end_time=time(17, 0),
        is_available=True
    )
    doctor_with_avail = doctor.add_availability(
        db, doctor_id=doctor_obj.id, availability=availability_in
    )
    assert len(doctor_with_avail.availabilities) > 0
    avail = doctor_with_avail.availabilities[0]
    assert avail.day_of_week == availability_in.day_of_week
    assert avail.start_time == availability_in.start_time
    assert avail.end_time == availability_in.end_time

# ------------------- APPOINTMENT -------------------
def test_create_appointment(db: Session):
    # Créer patient
    patient_in = PatientCreate(
        first_name="Appointment",
        last_name="Patient",
        date_of_birth=datetime(1990, 1, 1).date(),
        email="appointment.patient@example.com",
        phone="1234567890",
        address="123 Test St",
        insurance_provider="Test Insurance",
        insurance_id="TI123456"
    )
    patient_obj = patient.create(db, obj_in=patient_in)

    # Créer doctor
    doctor_in = DoctorCreate(
        first_name="Appointment",
        last_name="Doctor",
        email="appointment.doctor@example.com",
        phone="0987654321",
        specialization="Test Specialty"
    )
    doctor_obj = doctor.create(db, obj_in=doctor_in)

    # Ajouter disponibilité
    availability_in = AvailabilityCreate(
        day_of_week=1,
        start_time=time(9, 0),
        end_time=time(17, 0),
        is_available=True
    )
    doctor.add_availability(db, doctor_id=doctor_obj.id, availability=availability_in)

    # Définir date du rendez-vous au prochain mardi
    tomorrow = datetime.now() + timedelta(days=1)
    while tomorrow.weekday() != 1:  # 1 = mardi
        tomorrow += timedelta(days=1)

    start_time = tomorrow.replace(hour=10, minute=0, second=0, microsecond=0)
    end_time = tomorrow.replace(hour=10, minute=30, second=0, microsecond=0)

    appointment_in = AppointmentCreate(
        patient_id=patient_obj.id,
        doctor_id=doctor_obj.id,
        start_time=start_time,
        end_time=end_time,
        status=AppointmentStatus.SCHEDULED,
        notes="Test appointment"
    )

    appointment_obj = appointment.create(db, obj_in=appointment_in)
    assert appointment_obj.id is not None
    assert appointment_obj.patient_id == appointment_in.patient_id
    assert appointment_obj.doctor_id == appointment_in.doctor_id
    assert appointment_obj.status == appointment_in.status.value

# ------------------- USER -------------------
def test_user_authentication(db: Session):
    user_in = UserCreate(
        email="test.user@example.com",
        username="testuser",
        password="password123",
        role=UserRole.ADMIN
    )
    user_obj = user.create(db, obj_in=user_in)
    assert user_obj.id is not None
    assert user_obj.email == user_in.email

    authenticated_user = user.authenticate(db, email=user_in.email, password="password123")
    assert authenticated_user is not None
    assert authenticated_user.id == user_obj.id

    wrong_user = user.authenticate(db, email=user_in.email, password="wrongpassword")
    assert wrong_user is None