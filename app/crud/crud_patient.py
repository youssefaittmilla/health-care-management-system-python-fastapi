from typing import Optional, List
from datetime import datetime
from sqlalchemy.orm import Session
from app.db.models import Patient
from app.schemas.patient import PatientCreate, PatientUpdate

class CRUDPatient:
    def get_by_email(self, db: Session, *, email: str) -> Optional[Patient]:
        """Retourne un patient par email"""
        return db.query(Patient).filter(Patient.email == email).first()

    def get(self, db: Session, patient_id: int) -> Optional[Patient]:
        """Retourne un patient par ID"""
        return db.query(Patient).filter(Patient.id == patient_id).first()

    def get_all(self, db: Session, skip: int = 0, limit: int = 100) -> List[Patient]:
        """Retourne tous les patients"""
        return db.query(Patient).offset(skip).limit(limit).all()

    def create(self, db: Session, *, obj_in: PatientCreate) -> Patient:
        """Crée un patient"""
        # Convertir date_of_birth en date si nécessaire
        dob = obj_in.date_of_birth
        if isinstance(dob, str):
            from datetime import datetime
            dob = datetime.strptime(dob, "%Y-%m-%d").date()

        db_obj = Patient(
            first_name=obj_in.first_name,
            last_name=obj_in.last_name,
            date_of_birth=dob,
            email=obj_in.email,
            phone=obj_in.phone,
            address=obj_in.address,
            insurance_provider=obj_in.insurance_provider,
            insurance_id=obj_in.insurance_id
        )
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def update(self, db: Session, db_obj: Patient, *, obj_in: PatientUpdate) -> Patient:
        """Met à jour un patient existant"""
        update_data = obj_in.dict(exclude_unset=True)
        if 'date_of_birth' in update_data and isinstance(update_data['date_of_birth'], str):
            update_data['date_of_birth'] = datetime.strptime(update_data['date_of_birth'], "%Y-%m-%d").date()
        for field, value in update_data.items():
            setattr(db_obj, field, value)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def delete(self, db: Session, patient_id: int) -> Patient:
        """Supprime un patient par ID"""
        obj = db.query(Patient).filter(Patient.id == patient_id).first()
        if obj:
            db.delete(obj)
            db.commit()
        return obj

# Instance réutilisable
patient = CRUDPatient()