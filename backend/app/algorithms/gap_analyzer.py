from typing import Dict, Any, List
from sqlalchemy.orm import Session
from app.database.models import Student, CompletionRecord, Experiment, StudentBatch, BatchExperiment

def calculate_student_learning_gap(
    db: Session,
    experiment_id: int,
    batch_id: int = None
) -> Dict[str, Any]:
    """
    Computes practical learning gap for an experiment.
    Enforces rule: Attendance alone != practical competence.
    Only Completed + Verified records count as verified practical completion.
    """
    experiment = db.query(Experiment).filter(Experiment.id == experiment_id).first()
    if not experiment:
        return {"error": "Experiment not found"}

    # Query assigned students
    student_query = db.query(Student)
    if batch_id:
        student_query = student_query.filter(Student.batch_id == batch_id)
    else:
        # Get all batches assigned to this experiment
        assigned_batch_ids = [
            b.batch_id for b in db.query(BatchExperiment).filter(
                BatchExperiment.experiment_id == experiment_id
            ).all()
        ]
        if assigned_batch_ids:
            student_query = student_query.filter(Student.batch_id.in_(assigned_batch_ids))

    assigned_students = student_query.all()
    total_assigned = len(assigned_students)
    assigned_student_ids = [s.id for s in assigned_students]

    if not assigned_student_ids:
        return {
            "experiment_id": experiment_id,
            "experiment_name": experiment.name,
            "batch_id": batch_id,
            "total_assigned": 0,
            "scheduled": 0,
            "participated": 0,
            "partially_completed": 0,
            "verified_completed": 0,
            "unverified_learning_gap": 0,
            "gap_percentage": 0.0,
            "student_breakdown": []
        }

    # Fetch completion records for these students and experiment
    completions = db.query(CompletionRecord).filter(
        CompletionRecord.experiment_id == experiment_id,
        CompletionRecord.student_id.in_(assigned_student_ids)
    ).all()

    completion_map = {c.student_id: c for c in completions}

    verified_completed_count = 0
    partially_completed_count = 0
    participated_count = 0
    not_started_count = 0

    student_details = []
    for s in assigned_students:
        record = completion_map.get(s.id)
        if record:
            is_verified = (
                record.participation_status == "Completed" and
                record.verification_status == "Verified"
            )
            if is_verified:
                verified_completed_count += 1
                status_label = "Verified Competent"
            elif record.participation_status == "Partially completed":
                partially_completed_count += 1
                status_label = f"Partially Completed ({record.verification_status})"
            elif record.participation_status == "Completed" and record.verification_status != "Verified":
                participated_count += 1
                status_label = f"Pending Faculty Verification ({record.verification_status})"
            else:
                participated_count += 1
                status_label = f"Participated ({record.verification_status})"
            
            student_details.append({
                "student_id": s.id,
                "student_id_number": s.student_id_number,
                "student_name": s.name,
                "batch_id": s.batch_id,
                "batch_name": s.batch.batch_name if s.batch else "Unassigned",
                "participation_status": record.participation_status,
                "verification_status": record.verification_status,
                "is_verified": is_verified,
                "notes": record.assessment_notes,
                "status_label": status_label
            })
        else:
            not_started_count += 1
            student_details.append({
                "student_id": s.id,
                "student_id_number": s.student_id_number,
                "student_name": s.name,
                "batch_id": s.batch_id,
                "batch_name": s.batch.batch_name if s.batch else "Unassigned",
                "participation_status": "Not started",
                "verification_status": "Pending",
                "is_verified": False,
                "notes": None,
                "status_label": "Not Started / Pending Session"
            })

    unverified_gap = total_assigned - verified_completed_count
    gap_percentage = round((unverified_gap / total_assigned) * 100, 1) if total_assigned > 0 else 0.0

    return {
        "experiment_id": experiment.id,
        "experiment_code": experiment.experiment_code,
        "experiment_name": experiment.name,
        "batch_id": batch_id,
        "total_assigned": total_assigned,
        "participated": participated_count,
        "partially_completed": partially_completed_count,
        "verified_completed": verified_completed_count,
        "unverified_learning_gap": unverified_gap,
        "gap_percentage": gap_percentage,
        "student_breakdown": student_details
    }
