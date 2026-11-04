import datetime
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database.connection import get_db
from app.database.models import CompletionRecord, Student, Experiment, StudentBatch, Faculty, User
from app.schemas.schemas import CompletionRecordCreate, CompletionRecordVerify, CompletionRecordResponse
from app.security.permissions import require_faculty_or_admin, require_all_authenticated

router = APIRouter(prefix="/verification", tags=["Practical Verification"])

@router.get("/")
def list_completion_records(
    experiment_id: Optional[int] = None,
    batch_id: Optional[int] = None,
    verification_status: Optional[str] = None,
    current_user: User = Depends(require_all_authenticated),
    db: Session = Depends(get_db)
):
    query = db.query(CompletionRecord)
    if experiment_id:
        query = query.filter(CompletionRecord.experiment_id == experiment_id)
    if batch_id:
        query = query.filter(CompletionRecord.batch_id == batch_id)
    if verification_status:
        query = query.filter(CompletionRecord.verification_status == verification_status)

    records = query.all()
    results = []
    for r in records:
        student = db.query(Student).filter(Student.id == r.student_id).first()
        experiment = db.query(Experiment).filter(Experiment.id == r.experiment_id).first()
        batch = db.query(StudentBatch).filter(StudentBatch.id == r.batch_id).first()
        instructor = db.query(Faculty).filter(Faculty.id == r.instructor_id).first() if r.instructor_id else None

        results.append({
            "id": r.id,
            "student_id": r.student_id,
            "student_name": student.name if student else "Unknown",
            "student_id_number": student.student_id_number if student else "N/A",
            "experiment_id": r.experiment_id,
            "experiment_name": experiment.name if experiment else "Unknown",
            "experiment_code": experiment.experiment_code if experiment else "N/A",
            "batch_id": r.batch_id,
            "batch_code": batch.batch_code if batch else "N/A",
            "participation_status": r.participation_status,
            "verification_status": r.verification_status,
            "is_verified_competent": (r.participation_status == "Completed" and r.verification_status == "Verified"),
            "instructor_id": r.instructor_id,
            "instructor_name": instructor.name if instructor else "Unassigned",
            "verification_timestamp": r.verification_timestamp,
            "assessment_notes": r.assessment_notes,
            "created_at": r.created_at,
            "updated_at": r.updated_at
        })

    return results

@router.post("/record")
def record_student_participation(
    payload: CompletionRecordCreate,
    current_user: User = Depends(require_faculty_or_admin),
    db: Session = Depends(get_db)
):
    """
    Faculty records student practical performance.
    """
    student = db.query(Student).filter(Student.id == payload.student_id).first()
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")

    experiment = db.query(Experiment).filter(Experiment.id == payload.experiment_id).first()
    if not experiment:
        raise HTTPException(status_code=404, detail="Experiment not found")

    # Check for existing record
    record = db.query(CompletionRecord).filter(
        CompletionRecord.student_id == payload.student_id,
        CompletionRecord.experiment_id == payload.experiment_id
    ).first()

    instructor_id = None
    if current_user.faculty_profile:
        instructor_id = current_user.faculty_profile.id

    if record:
        if record.participation_status == "Completed" and record.verification_status == "Verified":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Student {student.name} already holds a verified practical completion record for {experiment.name}."
            )
        record.participation_status = payload.participation_status
        record.verification_status = "Pending"  # Requires explicit verification step
        record.instructor_id = instructor_id
        record.assessment_notes = payload.assessment_notes
        db.commit()
        db.refresh(record)
        return {"message": "Participation record updated", "id": record.id}
    else:
        new_record = CompletionRecord(
            student_id=payload.student_id,
            experiment_id=payload.experiment_id,
            batch_id=payload.batch_id,
            participation_status=payload.participation_status,
            verification_status="Pending",
            instructor_id=instructor_id,
            assessment_notes=payload.assessment_notes
        )
        db.add(new_record)
        db.commit()
        db.refresh(new_record)
        return {"message": "Participation recorded successfully", "id": new_record.id}

@router.put("/verify/{record_id}")
def verify_completion_record(
    record_id: int,
    payload: CompletionRecordVerify,
    current_user: User = Depends(require_faculty_or_admin),
    db: Session = Depends(get_db)
):
    """
    Faculty verifies or rejects practical completion.
    Strict enforcement: Students CANNOT verify their own completion.
    """
    record = db.query(CompletionRecord).filter(CompletionRecord.id == record_id).first()
    if not record:
        raise HTTPException(status_code=404, detail="Completion record not found")

    if payload.verification_status not in ["Verified", "Rejected", "Pending"]:
        raise HTTPException(status_code=400, detail="Invalid verification status. Must be Verified, Rejected, or Pending.")

    instructor_id = None
    if current_user.faculty_profile:
        instructor_id = current_user.faculty_profile.id

    record.verification_status = payload.verification_status
    if payload.verification_status == "Verified":
        # Ensure participation status is marked Completed upon verification
        record.participation_status = "Completed"
        record.verification_timestamp = datetime.datetime.utcnow()
    else:
        record.verification_timestamp = None

    if instructor_id:
        record.instructor_id = instructor_id

    if payload.assessment_notes:
        record.assessment_notes = payload.assessment_notes

    db.commit()
    db.refresh(record)

    return {
        "message": f"Practical completion {payload.verification_status.lower()} successfully",
        "record_id": record.id,
        "verification_status": record.verification_status,
        "verification_timestamp": record.verification_timestamp
    }
