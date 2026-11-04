from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database.connection import get_db
from app.database.models import Laboratory, Equipment, Experiment, Faculty, User
from app.schemas.schemas import LaboratoryCreate, LaboratoryUpdate, LaboratoryResponse
from app.security.permissions import require_admin, require_all_authenticated

router = APIRouter(prefix="/laboratories", tags=["Laboratories"])

@router.get("/", response_model=List[dict])
def list_laboratories(
    department_id: Optional[int] = None,
    current_user: User = Depends(require_all_authenticated),
    db: Session = Depends(get_db)
):
    query = db.query(Laboratory)
    if department_id:
        query = query.filter(Laboratory.department_id == department_id)
    labs = query.all()

    result = []
    for lab in labs:
        eq_count = db.query(Equipment).filter(Equipment.laboratory_id == lab.id).count()
        exp_count = db.query(Experiment).filter(Experiment.laboratory_id == lab.id).count()
        assigned_faculty = db.query(Faculty).filter(Faculty.id == lab.assigned_faculty_id).first() if lab.assigned_faculty_id else None

        result.append({
            "id": lab.id,
            "department_id": lab.department_id,
            "code": lab.code,
            "name": lab.name,
            "location": lab.location,
            "max_student_capacity": lab.max_student_capacity,
            "working_days": lab.working_days,
            "open_time": lab.open_time,
            "close_time": lab.close_time,
            "assigned_faculty_id": lab.assigned_faculty_id,
            "assigned_faculty_name": assigned_faculty.name if assigned_faculty else "Unassigned",
            "equipment_count": eq_count,
            "experiment_count": exp_count,
            "created_at": lab.created_at
        })
    return result

@router.get("/{lab_id}")
def get_laboratory(
    lab_id: int,
    current_user: User = Depends(require_all_authenticated),
    db: Session = Depends(get_db)
):
    lab = db.query(Laboratory).filter(Laboratory.id == lab_id).first()
    if not lab:
        raise HTTPException(status_code=404, detail="Laboratory not found")

    equipment = db.query(Equipment).filter(Equipment.laboratory_id == lab.id).all()
    experiments = db.query(Experiment).filter(Experiment.laboratory_id == lab.id).all()
    assigned_faculty = db.query(Faculty).filter(Faculty.id == lab.assigned_faculty_id).first() if lab.assigned_faculty_id else None

    return {
        "id": lab.id,
        "department_id": lab.department_id,
        "code": lab.code,
        "name": lab.name,
        "location": lab.location,
        "max_student_capacity": lab.max_student_capacity,
        "working_days": lab.working_days,
        "open_time": lab.open_time,
        "close_time": lab.close_time,
        "assigned_faculty_id": lab.assigned_faculty_id,
        "assigned_faculty_name": assigned_faculty.name if assigned_faculty else "Unassigned",
        "equipment": [{
            "id": e.id, "name": e.name, "code": e.equipment_code,
            "total": e.total_quantity, "functional": e.functional_quantity,
            "damaged": e.damaged_quantity, "under_maintenance": e.under_maintenance_quantity
        } for e in equipment],
        "experiments": [{
            "id": ex.id, "name": ex.name, "code": ex.experiment_code,
            "duration_hours": ex.duration_hours, "competency": ex.practical_competency
        } for ex in experiments]
    }

@router.post("/", response_model=LaboratoryResponse)
def create_laboratory(
    payload: LaboratoryCreate,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    existing = db.query(Laboratory).filter(Laboratory.code == payload.code).first()
    if existing:
        raise HTTPException(status_code=400, detail="Laboratory with this code already exists")

    lab = Laboratory(
        department_id=payload.department_id,
        code=payload.code,
        name=payload.name,
        location=payload.location,
        max_student_capacity=payload.max_student_capacity,
        working_days=payload.working_days,
        open_time=payload.open_time,
        close_time=payload.close_time,
        assigned_faculty_id=payload.assigned_faculty_id
    )
    db.add(lab)
    db.commit()
    db.refresh(lab)
    return lab

@router.put("/{lab_id}", response_model=LaboratoryResponse)
def update_laboratory(
    lab_id: int,
    payload: LaboratoryUpdate,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    lab = db.query(Laboratory).filter(Laboratory.id == lab_id).first()
    if not lab:
        raise HTTPException(status_code=404, detail="Laboratory not found")

    for field, val in payload.model_dump(exclude_unset=True).items():
        setattr(lab, field, val)

    db.commit()
    db.refresh(lab)
    return lab

@router.delete("/{lab_id}")
def delete_laboratory(
    lab_id: int,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    lab = db.query(Laboratory).filter(Laboratory.id == lab_id).first()
    if not lab:
        raise HTTPException(status_code=404, detail="Laboratory not found")

    db.delete(lab)
    db.commit()
    return {"message": "Laboratory deleted successfully"}
