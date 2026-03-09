import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from datetime import datetime, timedelta
from app.main import app
from app.db.models import Base
from app.db.session import get_db
from app.crud.crud_user import user
from app.schemas.user import UserCreate, UserRole

SQLALCHEMY_DATABASE_URL = "sqlite:///./test_api.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db
client = TestClient(app)

@pytest.fixture(scope="function", autouse=True)
def test_db():
    Base.metadata.create_all(bind=engine)  # CRÉE TOUTES LES TABLES
    yield
    Base.metadata.drop_all(bind=engine)

@pytest.fixture(scope="function")
def admin_token(test_db):
    # Créer l'admin APRÈS création des tables
    db = TestingSessionLocal()
    try:
        admin_user = UserCreate(
            email="admin@example.com",
            username="admin",
            password="password",
            role=UserRole.ADMIN
        )
        user.create(db, obj_in=admin_user)
    finally:
        db.close()

    response = client.post("/api/auth/login", json={"email": "admin@example.com", "password": "password"})
    assert response.status_code == 200
    return response.json()["access_token"]

@pytest.fixture(scope="function")
def patient_data(test_db, admin_token):
    data = {
        "first_name": "John", "last_name": "Doe", "date_of_birth": "1990-01-01",
        "email": "john.doe@example.com", "phone": "1234567890",
        "address": "123 Main St", "insurance_provider": "Blue Cross", "insurance_id": "BC123456"
    }
    response = client.post("/api/patients/", json=data, headers={"Authorization": f"Bearer {admin_token}"})
    assert response.status_code == 200
    return response.json()

@pytest.fixture(scope="function")
def doctor_data(test_db, admin_token):
    data = {
        "first_name": "Jane", "last_name": "Smith",
        "email": "jane.smith@example.com", "phone": "0987654321", "specialization": "Cardiology"
    }
    response = client.post("/api/doctors/", json=data, headers={"Authorization": f"Bearer {admin_token}"})
    assert response.status_code == 200
    doctor_id = response.json()["id"]
    
    # Ajouter disponibilité
    client.post(f"/api/doctors/{doctor_id}/availability", json={
        "day_of_week": 1, "start_time": "09:00:00", "end_time": "17:00:00", "is_available": True
    }, headers={"Authorization": f"Bearer {admin_token}"})
    return response.json()

def test_health_check():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"

def test_create_patient(admin_token):
    data = {
        "first_name": "Alice", "last_name": "Johnson", "date_of_birth": "1985-05-15",
        "email": "alice.johnson@example.com", "phone": "5551234567",
        "address": "456 Oak St", "insurance_provider": "Aetna", "insurance_id": "AE789012"
    }
    response = client.post("/api/patients/", json=data, headers={"Authorization": f"Bearer {admin_token}"})
    assert response.status_code == 200
    assert response.json()["first_name"] == "Alice"

def test_create_doctor(admin_token):
    data = {
        "first_name": "Robert", "last_name": "Williams",
        "email": "robert.williams@example.com", "phone": "5559876543", "specialization": "Neurology"
    }
    response = client.post("/api/doctors/", json=data, headers={"Authorization": f"Bearer {admin_token}"})
    assert response.status_code == 200
    assert response.json()["specialization"] == "Neurology"

def test_create_appointment(admin_token, patient_data, doctor_data):
    dt = datetime.now()
    for _ in range(14):
        dt += timedelta(days=1)
        if dt.weekday() == 1:  # Mardi
            break
    start_time = dt.replace(hour=10, minute=0, second=0, microsecond=0).isoformat()
    end_time = dt.replace(hour=10, minute=30, second=0, microsecond=0).isoformat()

    data = {
        "patient_id": patient_data["id"], "doctor_id": doctor_data["id"],
        "start_time": start_time, "end_time": end_time,
        "status": "scheduled", "notes": "Regular checkup"
    }
    response = client.post("/api/appointments/", json=data, headers={"Authorization": f"Bearer {admin_token}"})
    assert response.status_code == 200
    assert response.json()["status"] == "scheduled"
