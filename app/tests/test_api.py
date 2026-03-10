import pytest
from fastapi.testclient import TestClient
from unittest.mock import MagicMock
from datetime import date, datetime
from app.main import app
from app.api.deps import get_db, get_current_user, get_current_active_user

# Helper : objets SQLAlchemy-like COMPLETS
def make_patient(overrides=None):
    obj = MagicMock()
    obj.id = 1
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
    obj.id = 1
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

@pytest.fixture
def client():
    # ✅ 1. Mock User ADMIN (POUR 401)
    mock_user = MagicMock()
    mock_user.is_active = True
    mock_user.role = "admin"
    
    # ✅ 2. Mock DB
    mock_db = MagicMock()
    
    # ✅ 3. Dependency Overrides DIRECTS (100% sûr)
    app.dependency_overrides = {
        get_db: lambda: mock_db,
        get_current_user: lambda: mock_user,
        get_current_active_user: lambda: mock_user
    }
    
    # ✅ 4. Mock CRUD returns
    with (
        patch('app.crud.crud_patient.patient.create', return_value=make_patient()),
        patch('app.crud.crud_patient.patient.get_by_email', return_value=None),
        patch('app.crud.crud_doctor.doctor.create', return_value=make_doctor()),
        patch('app.crud.crud_doctor.doctor.get_by_email', return_value=None),
        patch('app.crud.crud_appointment.appointment.create', return_value=make_patient())
    ):
        yield TestClient(app)
    
    # Cleanup
    app.dependency_overrides.clear()

# Tests identiques
def test_health_check(client):
    response = client.get("/health")
    assert response.status_code == 200

def test_create_patient(client):
    data = {
        "first_name": "Alice", "last_name": "Johnson",
        "date_of_birth": "1985-05-15", "email": "alice@test.com",
        "phone": "1234567890", "address": "123 Test St",
        "insurance_provider": "Test Ins", "insurance_id": "TEST123"
    }
    response = client.post("/api/patients/", json=data)
    assert response.status_code == 200

def test_create_doctor(client):
    data = {
        "first_name": "Dr", "last_name": "Test",
        "email": "doctor@test.com", "phone": "0987654321",
        "specialization": "Cardiology"
    }
    response = client.post("/api/doctors/", json=data)
    assert response.status_code == 200

@pytest.fixture
def patient_data(client):
    data = {
        "first_name": "John", "last_name": "Doe",
        "date_of_birth": "1990-01-01", "email": "john@test.com",
        "phone": "1234567890", "address": "123 Test St",
        "insurance_provider": "Test Ins", "insurance_id": "TEST123"
    }
    response = client.post("/api/patients/", json=data)
    assert response.status_code == 200
    return {"id": 1}  # Simplifié

@pytest.fixture
def doctor_data(client):
    data = {
        "first_name": "Jane", "last_name": "Doe",
        "email": "jane@test.com", "phone": "0987654321",
        "specialization": "Cardiology"
    }
    response = client.post("/api/doctors/", json=data)
    assert response.status_code == 200
    return {"id": 1}  # Simplifié

def test_create_appointment(client, patient_data, doctor_data):
    from datetime import datetime, timedelta
    dt = datetime.now()
    for _ in range(14):
        dt += timedelta(days=1)
        if dt.weekday() == 1: break
    
    data = {
        "patient_id": 1, "doctor_id": 1,
        "start_time": dt.replace(hour=10).isoformat(),
        "end_time": dt.replace(hour=10, minute=30).isoformat(),
        "status": "scheduled"
    }
    response = client.post("/api/appointments/", json=data)
    assert response.status_code == 200
