from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database.connection import get_db
from app.database.models import Student, StudentBatch, Experiment, BatchExperiment, CompletionRecord, Schedule, User
from app.schemas.schemas import StudentCreate, StudentResponse
from app.security.permissions import require_admin, require_all_authenticated

router = APIRouter(prefix="/students", tags=["Students"])

@router.get("/")
def list_students(
    batch_id: Optional[int] = None,
    search: Optional[str] = None,
    current_user: User = Depends(require_all_authenticated),
    db: Session = Depends(get_db)
):
    query = db.query(Student)
    if batch_id:
        query = query.filter(Student.batch_id == batch_id)
    if search:
        query = query.filter(
            (Student.name.ilike(f"%{search}%")) |
            (Student.student_id_number.ilike(f"%{search}%")) |
            (Student.email.ilike(f"%{search}%"))
        )

    students = query.all()
    results = []
    for s in students:
        total_completions = db.query(CompletionRecord).filter(
            CompletionRecord.student_id == s.id,
            CompletionRecord.participation_status == "Completed",
            CompletionRecord.verification_status == "Verified"
        ).count()

        results.append({
            "id": s.id,
            "student_id_number": s.student_id_number,
            "name": s.name,
            "email": s.email,
            "department_id": s.department_id,
            "batch_id": s.batch_id,
            "batch_code": s.batch.batch_code if s.batch else "Unassigned",
            "batch_name": s.batch.batch_name if s.batch else "Unassigned",
            "verified_completions_count": total_completions,
            "created_at": s.created_at
        })
    return results

@router.get("/portal/{student_id}")
def get_student_portal_data(
    student_id: int,
    current_user: User = Depends(require_all_authenticated),
    db: Session = Depends(get_db)
):
    # If the user is a student, ensure they only access their own profile!
    if current_user.role and current_user.role.name == "student":
        if not current_user.student_profile or current_user.student_profile.id != student_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied: Students can only view their own practical portal."
            )

    student = db.query(Student).filter(Student.id == student_id).first()
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")

    batch = student.batch
    assigned_experiments = []
    if batch:
        exp_links = db.query(BatchExperiment).filter(BatchExperiment.batch_id == batch.id).all()
        for link in exp_links:
            exp = db.query(Experiment).filter(Experiment.id == link.experiment_id).first()
            if exp:
                assigned_experiments.append(exp)

    # Fetch completion records
    completions = db.query(CompletionRecord).filter(CompletionRecord.student_id == student.id).all()
    completion_map = {c.experiment_id: c for c in completions}

    experiment_status_list = []
    verified_count = 0
    pending_count = 0

    for exp in assigned_experiments:
        rec = completion_map.get(exp.id)
        if rec:
            is_verified = (rec.participation_status == "Completed" and rec.verification_status == "Verified")
            if is_verified:
                verified_count += 1
                status_badge = "Verified Competent"
            elif rec.verification_status == "Rejected":
                status_badge = "Verification Rejected - Re-attempt Required"
                pending_count += 1
            else:
                status_badge = f"{rec.participation_status} ({rec.verification_status})"
                pending_count += 1

            experiment_status_list.append({
                "experiment_id": exp.id,
                "experiment_code": exp.experiment_code,
                "experiment_name": exp.name,
                "laboratory_name": exp.laboratory.name if exp.laboratory else "N/A",
                "practical_competency": exp.practical_competency,
                "duration_hours": exp.duration_hours,
                "participation_status": rec.participation_status,
                "verification_status": rec.verification_status,
                "is_verified": is_verified,
                "status_badge": status_badge,
                "instructor_notes": rec.assessment_notes,
                "verification_timestamp": rec.verification_timestamp
            })
        else:
            pending_count += 1
            experiment_status_list.append({
                "experiment_id": exp.id,
                "experiment_code": exp.experiment_code,
                "experiment_name": exp.name,
                "laboratory_name": exp.laboratory.name if exp.laboratory else "N/A",
                "practical_competency": exp.practical_competency,
                "duration_hours": exp.duration_hours,
                "participation_status": "Not started",
                "verification_status": "Pending",
                "is_verified": False,
                "status_badge": "Not Started / Pending Laboratory Session",
                "instructor_notes": None,
                "verification_timestamp": None
            })

    # Upcoming schedules for student's batch
    upcoming_schedules = []
    if batch:
        scheds = db.query(Schedule).filter(Schedule.batch_id == batch.id).order_date_by = db.query(Schedule).filter(
            Schedule.batch_id == batch.id
        ).all()
        for s in scheds:
            upcoming_schedules.append({
                "id": s.id,
                "experiment_name": s.experiment.name if s.experiment else "Experiment",
                "laboratory_name": s.experiment.laboratory.name if (s.experiment and s.experiment.laboratory) else "Lab",
                "date": s.date,
                "start_time": s.start_time,
                "end_time": s.end_time,
                "faculty_name": s.faculty_id if s.faculty_id else "Faculty Instructor"
            })

    total_assigned = len(assigned_experiments)
    completion_rate = round((verified_count / total_assigned) * 100, 1) if total_assigned > 0 else 0.0

    return {
        "student_id": student.id,
        "student_id_number": student.student_id_number,
        "name": student.name,
        "email": student.email,
        "department_name": student.department.name if student.department else "Engineering",
        "batch_id": student.batch_id,
        "batch_code": batch.batch_code if batch else "Unassigned",
        "batch_name": batch.batch_name if batch else "Unassigned",
        "total_assigned_experiments": total_assigned,
        "verified_completed_count": verified_count,
        "pending_experiments_count": pending_count,
        "completion_rate_percentage": completion_rate,
        "experiments": experiment_status_list,
        "upcoming_schedules": upcoming_schedules
    }
