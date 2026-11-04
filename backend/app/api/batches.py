from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database.connection import get_db
from app.database.models import StudentBatch, Student, BatchExperiment, Experiment, Faculty, Laboratory, User
from app.schemas.schemas import StudentBatchCreate, StudentBatchResponse
from app.security.permissions import require_admin, require_faculty_or_admin, require_all_authenticated

router = APIRouter(prefix="/batches", tags=["Student Batches"])

@router.get("/")
def list_batches(
    laboratory_id: Optional[int] = None,
    current_user: User = Depends(require_all_authenticated),
    db: Session = Depends(get_db)
):
    query = db.query(StudentBatch)
    if laboratory_id:
        query = query.filter(StudentBatch.laboratory_id == laboratory_id)

    batches = query.all()
    results = []
    for b in batches:
        student_count = db.query(Student).filter(Student.batch_id == b.id).count()
        # update number_of_students if different
        if b.number_of_students != student_count and student_count > 0:
            b.number_of_students = student_count
            db.commit()

        exp_links = db.query(BatchExperiment).filter(BatchExperiment.batch_id == b.id).all()
        assigned_exps = []
        for el in exp_links:
            exp = db.query(Experiment).filter(Experiment.id == el.experiment_id).first()
            if exp:
                assigned_exps.append({"id": exp.id, "name": exp.name, "code": exp.experiment_code})

        faculty = db.query(Faculty).filter(Faculty.id == b.assigned_faculty_id).first() if b.assigned_faculty_id else None

        results.append({
            "id": b.id,
            "department_id": b.department_id,
            "laboratory_id": b.laboratory_id,
            "laboratory_name": b.laboratory.name if b.laboratory else "Unassigned",
            "batch_code": b.batch_code,
            "batch_name": b.batch_name,
            "number_of_students": b.number_of_students,
            "assigned_faculty_id": b.assigned_faculty_id,
            "assigned_faculty_name": faculty.name if faculty else "Unassigned",
            "assigned_experiments": assigned_exps,
            "created_at": b.created_at
        })

    return results

@router.get("/{batch_id}")
def get_batch_detail(
    batch_id: int,
    current_user: User = Depends(require_all_authenticated),
    db: Session = Depends(get_db)
):
    b = db.query(StudentBatch).filter(StudentBatch.id == batch_id).first()
    if not b:
        raise HTTPException(status_code=404, detail="Batch not found")

    students = db.query(Student).filter(Student.batch_id == b.id).all()
    exp_links = db.query(BatchExperiment).filter(BatchExperiment.batch_id == b.id).all()
    assigned_exps = []
    for el in exp_links:
        exp = db.query(Experiment).filter(Experiment.id == el.experiment_id).first()
        if exp:
            assigned_exps.append({
                "id": exp.id,
                "name": exp.name,
                "code": exp.experiment_code,
                "duration_hours": exp.duration_hours,
                "competency": exp.practical_competency
            })

    faculty = db.query(Faculty).filter(Faculty.id == b.assigned_faculty_id).first() if b.assigned_faculty_id else None

    return {
        "id": b.id,
        "department_id": b.department_id,
        "laboratory_id": b.laboratory_id,
        "laboratory_name": b.laboratory.name if b.laboratory else "Unassigned",
        "batch_code": b.batch_code,
        "batch_name": b.batch_name,
        "number_of_students": len(students),
        "assigned_faculty_id": b.assigned_faculty_id,
        "assigned_faculty_name": faculty.name if faculty else "Unassigned",
        "assigned_experiments": assigned_exps,
        "students": [{
            "id": s.id, "student_id_number": s.student_id_number,
            "name": s.name, "email": s.email
        } for s in students]
    }

@router.post("/", response_model=StudentBatchResponse)
def create_batch(
    payload: StudentBatchCreate,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    existing = db.query(StudentBatch).filter(StudentBatch.batch_code == payload.batch_code).first()
    if existing:
        raise HTTPException(status_code=400, detail="Batch code already exists")

    batch = StudentBatch(
        department_id=payload.department_id,
        laboratory_id=payload.laboratory_id,
        batch_code=payload.batch_code,
        batch_name=payload.batch_name,
        number_of_students=payload.number_of_students,
        assigned_faculty_id=payload.assigned_faculty_id
    )
    db.add(batch)
    db.commit()
    db.refresh(batch)
    return batch

@router.post("/{batch_id}/assign-experiments")
def assign_experiments_to_batch(
    batch_id: int,
    experiment_ids: List[int],
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    batch = db.query(StudentBatch).filter(StudentBatch.id == batch_id).first()
    if not batch:
        raise HTTPException(status_code=404, detail="Batch not found")

    # Remove existing
    db.query(BatchExperiment).filter(BatchExperiment.batch_id == batch_id).delete()

    for exp_id in experiment_ids:
        link = BatchExperiment(batch_id=batch_id, experiment_id=exp_id)
        db.add(link)

    db.commit()
    return {"message": f"Assigned {len(experiment_ids)} experiments to batch {batch.batch_code}"}
