from sqlalchemy.orm import Session
from app.db.models import Patient
from app.schemas.patient import PatientCreate, PatientUpdate

class CRUDPatient:
    def get(self, db: Session, patient_id: int):
        return db.query(Patient).filter(Patient.id == patient_id).first()

    def get_all(self, db: Session, skip: int = 0, limit: int = 100):
        return db.query(Patient).offset(skip).limit(limit).all()

    def create(self, db: Session, obj_in: PatientCreate):
        try:
            obj_data = obj_in.model_dump()
        except AttributeError:
            obj_data = obj_in.dict()
        db_obj = Patient(**obj_data)
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def update(self, db: Session, db_obj: Patient, obj_in: PatientUpdate):
        try:
            update_data = obj_in.model_dump(exclude_unset=True)
        except AttributeError:
            update_data = obj_in.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_obj, field, value)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def delete(self, db: Session, db_obj: Patient):
        db.delete(db_obj)
        db.commit()
        return db_obj

patient = CRUDPatient()
