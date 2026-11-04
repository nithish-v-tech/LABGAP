from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database.connection import get_db
from app.database.models import Faculty, Laboratory, StudentBatch, Experiment, CompletionRecord, Schedule, User, Role
from app.schemas.schemas import FacultyCreate, FacultyResponse
from app.security.auth import hash_password
from app.security.permissions import require_admin, require_faculty_or_admin, require_all_authenticated

router = APIRouter(prefix="/faculty", tags=["Faculty"])

@router.get("/")
def list_faculty(
    current_user: User = Depends(require_all_authenticated),
    db: Session = Depends(get_db)
):
    faculty_members = db.query(Faculty).all()
    results = []
    for f in faculty_members:
        lab = db.query(Laboratory).filter(Laboratory.id == f.assigned_laboratory_id).first() if f.assigned_laboratory_id else None
        batches = db.query(StudentBatch).filter(StudentBatch.assigned_faculty_id == f.id).all()
        pending_verifications = db.query(CompletionRecord).filter(
            CompletionRecord.instructor_id == f.id,
            CompletionRecord.verification_status == "Pending"
        ).count()

        results.append({
            "id": f.id,
            "faculty_code": f.faculty_code,
            "name": f.name,
            "email": f.email,
            "department_id": f.department_id,
            "assigned_laboratory_id": f.assigned_laboratory_id,
            "assigned_laboratory_name": lab.name if lab else "Unassigned",
            "assigned_batches_count": len(batches),
            "pending_verifications_count": pending_verifications,
            "created_at": f.created_at
        })
    return results

@router.get("/{faculty_id}/dashboard")
def get_faculty_dashboard(
    faculty_id: int,
    current_user: User = Depends(require_faculty_or_admin),
    db: Session = Depends(get_db)
):
    faculty = db.query(Faculty).filter(Faculty.id == faculty_id).first()
    if not faculty:
        raise HTTPException(status_code=404, detail="Faculty member not found")

    lab = db.query(Laboratory).filter(Laboratory.id == faculty.assigned_laboratory_id).first() if faculty.assigned_laboratory_id else None
    batches = db.query(StudentBatch).filter(StudentBatch.assigned_faculty_id == faculty.id).all()
    schedules = db.query(Schedule).filter(Schedule.faculty_id == faculty.id).all()

    # Pending verifications: records where verification_status == 'Pending' in batches/experiments assigned to faculty or all pending
    pending_records = db.query(CompletionRecord).filter(
        CompletionRecord.verification_status == "Pending"
    ).all()

    pending_list = []
    for r in pending_records:
        pending_list.append({
            "id": r.id,
            "student_id": r.student_id,
            "student_name": r.student.name if r.student else "Student",
            "student_id_number": r.student.student_id_number if r.student else "N/A",
            "experiment_id": r.experiment_id,
            "experiment_name": r.experiment.name if r.experiment else "Experiment",
            "batch_id": r.batch_id,
            "batch_code": r.batch.batch_code if r.batch else "Batch",
            "participation_status": r.participation_status,
            "verification_status": r.verification_status,
            "notes": r.assessment_notes,
            "created_at": r.created_at
        })

    return {
        "faculty_id": faculty.id,
        "name": faculty.name,
        "email": faculty.email,
        "assigned_laboratory": {"id": lab.id, "name": lab.name, "code": lab.code} if lab else None,
        "assigned_batches": [{
            "id": b.id, "batch_code": b.batch_code, "batch_name": b.batch_name, "students": b.number_of_students
        } for b in batches],
        "upcoming_schedules": [{
            "id": s.id, "date": s.date, "start_time": s.start_time, "end_time": s.end_time,
            "experiment_name": s.experiment.name if s.experiment else "Experiment",
            "laboratory_name": s.experiment.laboratory.name if (s.experiment and s.experiment.laboratory) else "Lab",
            "expected_students": s.expected_students
        } for s in schedules],
        "pending_verifications_count": len(pending_list),
        "pending_verifications": pending_list
    }
