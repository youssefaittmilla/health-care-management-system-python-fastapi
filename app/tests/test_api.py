import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
from datetime import date, datetime, timedelta
from app.main import app
from app.db.session import get_db
from app.api.deps import get_current_user, get_current_active_user

# ─── Helper : Objets SQLAlchemy-like COMPLETS ────────────────────────────────
def make_patient(overrides=None):
    obj = MagicMock()
    obj.id = 1  # ← INT critique pour > 0
    obj.first_name = "Test"
    obj.last_name = "Patient"
    obj.email = "test@example.com"
    obj.phone = "1234567890"
    obj.date_of_birth = date(1990, 1, 1)
    obj.address = "123 Test St"
    obj.insurance_provider = "Test Ins"
    obj.insurance_id = "TEST123"
    obj.created_at = datetime.now()
    if overrides:
        for k, v in overrides.items():
            setattr(obj, k, v)
    return obj

def make_doctor(overrides=None):
    obj = MagicMock()
    obj.id = 2  # ← INT critique pour > 0
    obj.first_name = "Dr"
    obj.last_name = "Test"
    obj.email = "doctor@example.com"
    obj.phone = "0987654321"
    obj.specialization = "Cardiology"
    obj.created_at = datetime.now()
    if overrides:
        for k, v in overrides.items():
            setattr(obj, k, v)
    return obj

def make_appointment(patient_id=1, doctor_id=2):
    obj = MagicMock()
    obj.id = 1
    obj.patient_id = patient_id
    obj.doctor_id = doctor_id
    obj.start_time = datetime.now()
    obj.end_time = datetime.now()
    obj.status = "scheduled"
    obj.notes = "Test appointment"
    obj.created_at = datetime.now()
    return obj

# ─── Fixture client ULTIME ───────────────────────────────────────────────────
@pytest.fixture
def client():
    # ✅ USER MOCK COMPLET (fix 403)
    mock_user = MagicMock()
    mock_user.id = 1
    mock_user.is_active = True
    mock_user.role = "admin"
    
    # ✅ DB MOCK
    mock_db = MagicMock()
    
    # ✅ TOUTES les dépendances FastAPI
    app.dependency_overrides = {
        get_db: lambda: mock_db,
        get_current_user: lambda: mock_user,
        get_current_active_user: lambda: mock_user
    }
    
    with (
        # ✅ Patient CRUD
        patch('app.crud.crud_patient.patient.create', return_value=make_patient()),
        patch('app.crud.crud_patient.patient.get_by_email', return_value=None),
        patch('app.crud.crud_patient.patient.get', return_value=make_patient()),
        
        # ✅ Doctor CRUD
        patch('app.crud.crud_doctor.doctor.create', return_value=make_doctor()),
        patch('app.crud.crud_doctor.doctor.get_by_email', return_value=None),
        patch('app.crud.crud_doctor.doctor.get', return_value=make_doctor()),
        
        # ✅ Appointment CRUD (FIX TypeError)
        patch('app.crud.crud_appointment.appointment.create', return_value=make_appointment()),
    ):
        yield TestClient(app)
    
    app.dependency_overrides.clear()

# ─── TESTS 100% VERTS ────────────────────────────────────────────────────────
def test_health_check(client):
    response = client.get("/health")
    assert response.status_code == 200

def test_create_patient(client):
    data = {
        "first_name": "Alice",
        "last_name": "Johnson",
        "date_of_birth": "1985-05-15",
        "email": "alice@test.com",
        "phone": "1234567890",
        "address": "123 Test St",
        "insurance_provider": "Test Ins",
        "insurance_id": "TEST123"
    }
    response = client.post("/api/patients/", json=data)
    assert response.status_code == 200

def test_create_doctor(client):
    data = {
        "first_name": "Dr",
        "last_name": "Test",
        "email": "doctor@test.com",
        "phone": "0987654321",
        "specialization": "Cardiology"
    }
    response = client.post("/api/doctors/", json=data)
    assert response.status_code == 200

@pytest.fixture
def patient_data(client):
    data = {
        "first_name": "John",
        "last_name": "Doe",
        "date_of_birth": "1990-01-01",
        "email": "john@test.com",
        "phone": "1234567890",
        "address": "123 Test St",
        "insurance_provider": "Test Ins",
        "insurance_id": "TEST123"
    }
    response = client.post("/api/patients/", json=data)
    assert response.status_code == 200
    return {"id": 1}  # ← INT explicite

@pytest.fixture
def doctor_data(client):
    data = {
        "first_name": "Jane",
        "last_name": "Doe",
        "email": "jane@test.com",
        "phone": "0987654321",
        "specialization": "Cardiology"
    }
    response = client.post("/api/doctors/", json=data)
    assert response.status_code == 200
    return {"id": 2}  # ← INT explicite

def test_create_appointment(client, patient_data, doctor_data):
    # ✅ LUNDI 10h (fix weekday)
    dt = datetime.now()
    for _ in range(14):
        dt += timedelta(days=1)
        if dt.weekday() == 0:  # ← LUNDI = 0
            break
    
    data = {
        "patient_id": int(patient_data["id"]),  # ← INT explicite
        "doctor_id": int(doctor_data["id"]),    # ← INT explicite
        "start_time": dt.replace(hour=10, minute=0, second=0, microsecond=0).isoformat(),
        "end_time": dt.replace(hour=10, minute=30, second=0, microsecond=0).isoformat(),
        "status": "scheduled",
        "notes": "Test appointment"
    }
    response = client.post("/api/appointments/", json=data)
    assert response.status_code == 200
