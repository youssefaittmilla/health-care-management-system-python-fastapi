import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
from datetime import datetime
from app.main import app

@pytest.fixture
def client():
    # ✅ DICTIONNAIRE Pydantic-compatible (100% sûr)
    mock_patient_response = {
        "id": 1,
        "first_name": "Test",
        "last_name": "Patient", 
        "email": "test@example.com",
        "phone": "1234567890",
        "date_of_birth": "1990-01-01",
        "address": "123 Test St",
        "insurance_provider": "Test Ins",
        "insurance_id": "TEST123",
        "created_at": datetime.now().isoformat()
    }
    
    mock_doctor_response = {
        "id": 1,
        "first_name": "Dr",
        "last_name": "Test", 
        "email": "doctor@example.com",
        "phone": "0987654321",
        "specialization": "Cardiology",
        "created_at": datetime.now().isoformat()
    }
    
    with (
        patch('app.crud.crud_patient.patient.create', return_value=mock_patient_response),
        patch('app.crud.crud_doctor.doctor.create', return_value=mock_doctor_response),
        patch('app.api.deps.get_db'),
        patch('app.api.deps.get_current_user', return_value=MagicMock(role="admin")),
        patch('app.api.deps.get_current_active_user', return_value=MagicMock(role="admin"))
    ):
        yield TestClient(app)

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
    return response.json()

@pytest.fixture
def doctor_data(client):
    data = {
        "first_name": "Jane", "last_name": "Doe",
        "email": "jane@test.com", "phone": "0987654321",
        "specialization": "Cardiology"
    }
    response = client.post("/api/doctors/", json=data)
    assert response.status_code == 200
    return response.json()

def test_create_appointment(client, patient_data, doctor_data):
    from datetime import datetime, timedelta
    dt = datetime.now()
    for _ in range(14):
        dt += timedelta(days=1)
        if dt.weekday() == 1: break
    
    data = {
        "patient_id": patient_data["id"],
        "doctor_id": doctor_data["id"],
        "start_time": dt.replace(hour=10).isoformat(),
        "end_time": dt.replace(hour=10, minute=30).isoformat(),
        "status": "scheduled",
        "notes": "Test appointment"
    }
    response = client.post("/api/appointments/", json=data)
    assert response.status_code == 200
