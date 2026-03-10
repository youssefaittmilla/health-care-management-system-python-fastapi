import pytest
from fastapi.testclient import TestClient
from unittest.mock import MagicMock
from app.main import app
from app.api.deps import get_db

@pytest.fixture
def client():
    # Mock Session COMPLET qui marche À COUP SÛR
    mock_session = MagicMock()
    mock_session.query.return_value.filter.return_value.first.return_value = None
    mock_session.add.return_value = None
    mock_session.commit.return_value = None
    mock_session.refresh.return_value = None
    mock_session.delete.return_value = None
    mock_session.close.return_value = None
    
    def override_get_db():
        return mock_session
    
    app.dependency_overrides[get_db] = override_get_db
    yield TestClient(app)
    app.dependency_overrides.clear()

@pytest.fixture
def admin_token(client):
    # Mock auth aussi
    app.dependency_overrides.clear()
    yield "fake-jwt-token-for-tests"
    app.dependency_overrides.clear()

def test_health_check(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"

def test_create_patient(client, admin_token):
    data = {
        "first_name": "Alice", "last_name": "Johnson",
        "date_of_birth": "1985-05-15", "email": "alice@example.com",
        "phone": "5551234567", "address": "456 Oak St",
        "insurance_provider": "Aetna", "insurance_id": "AE789012"
    }
    response = client.post("/api/patients/", json=data, headers={
        "Authorization": f"Bearer {admin_token}"
    })
    assert response.status_code == 200

def test_create_doctor(client, admin_token):
    data = {
        "first_name": "Robert", "last_name": "Williams",
        "email": "robert@example.com", "phone": "5559876543",
        "specialization": "Neurology"
    }
    response = client.post("/api/doctors/", json=data, headers={
        "Authorization": f"Bearer {admin_token}"
    })
    assert response.status_code == 200

@pytest.fixture
def patient_data(client, admin_token):
    data = {
        "first_name": "John", "last_name": "Doe",
        "date_of_birth": "1990-01-01", "email": "john@example.com",
        "phone": "1234567890", "address": "123 Main St",
        "insurance_provider": "Blue Cross", "insurance_id": "BC123456"
    }
    response = client.post("/api/patients/", json=data, headers={
        "Authorization": f"Bearer {admin_token}"
    })
    assert response.status_code == 200
    data["id"] = 1  # Mock ID
    return data

@pytest.fixture
def doctor_data(client, admin_token):
    data = {
        "first_name": "Jane", "last_name": "Smith",
        "email": "jane@example.com", "phone": "0987654321",
        "specialization": "Cardiology"
    }
    response = client.post("/api/doctors/", json=data, headers={
        "Authorization": f"Bearer {admin_token}"
    })
    assert response.status_code == 200
    data["id"] = 1
    return data

def test_create_appointment(client, admin_token, patient_data, doctor_data):
    from datetime import datetime, timedelta
    dt = datetime.now()
    for _ in range(14):
        dt += timedelta(days=1)
        if dt.weekday() == 1: break
    
    start_time = dt.replace(hour=10, minute=0).isoformat()
    end_time = dt.replace(hour=10, minute=30).isoformat()

    data = {
        "patient_id": patient_data["id"],
        "doctor_id": doctor_data["id"],
        "start_time": start_time,
        "end_time": end_time,
        "status": "scheduled",
        "notes": "Regular checkup"
    }
    response = client.post("/api/appointments/", json=data, headers={
        "Authorization": f"Bearer {admin_token}"
    })
    assert response.status_code == 200
