from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database.connection import get_db
from app.database.models import Schedule, Experiment, StudentBatch, Laboratory, Faculty, User, BatchExperiment
from app.schemas.schemas import ScheduleCreateRequest, ScheduleResponse, AutoAllocateRequest, ApproveAllocationRequest
from app.security.permissions import require_admin, require_all_authenticated
from app.algorithms.scheduling_engine import generate_optimized_schedule, auto_allocate_cohort_curriculum
from app.algorithms.smart_allocation_engine import evaluate_smart_laboratory_allocations

router = APIRouter(prefix="/schedule", tags=["Schedule Optimization"])

@router.get("/")
def list_schedules(
    laboratory_id: Optional[int] = None,
    batch_id: Optional[int] = None,
    experiment_id: Optional[int] = None,
    date: Optional[str] = None,
    current_user: User = Depends(require_all_authenticated),
    db: Session = Depends(get_db)
):
    query = db.query(Schedule)
    if laboratory_id:
        query = query.filter(Schedule.laboratory_id == laboratory_id)
    if batch_id:
        query = query.filter(Schedule.batch_id == batch_id)
    if experiment_id:
        query = query.filter(Schedule.experiment_id == experiment_id)
    if date:
        query = query.filter(Schedule.date == date)

    schedules = query.order_by(Schedule.date, Schedule.start_time).all()
    results = []
    for s in schedules:
        exp = db.query(Experiment).filter(Experiment.id == s.experiment_id).first()
        batch = db.query(StudentBatch).filter(StudentBatch.id == s.batch_id).first()
        lab = db.query(Laboratory).filter(Laboratory.id == s.laboratory_id).first()
        faculty = db.query(Faculty).filter(Faculty.id == s.faculty_id).first() if s.faculty_id else None

        results.append({
            "id": s.id,
            "session_number": s.session_number,
            "date": s.date,
            "start_time": s.start_time,
            "end_time": s.end_time,
            "experiment_id": s.experiment_id,
            "experiment_code": exp.experiment_code if exp else "N/A",
            "experiment_name": exp.name if exp else "N/A",
            "batch_id": s.batch_id,
            "batch_code": batch.batch_code if batch else "N/A",
            "laboratory_id": s.laboratory_id,
            "laboratory_name": lab.name if lab else "N/A",
            "faculty_id": s.faculty_id,
            "faculty_name": faculty.name if faculty else "Unassigned",
            "student_capacity": s.student_capacity,
            "expected_students": s.expected_students,
            "remaining_learning_gap": s.remaining_learning_gap,
            "status": s.status,
            "created_at": s.created_at
        })

    return results

@router.post("/optimize")
def generate_schedule_plan(
    payload: ScheduleCreateRequest,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """
    Executes the constraint-based scheduling engine to allocate feasible student rotation sessions.
    Saves generated sessions to the database.
    """
    result = generate_optimized_schedule(
        db,
        experiment_id=payload.experiment_id,
        batch_id=payload.batch_id,
        start_date=payload.start_date
    )

    if not result.get("success"):
        return result

    # Save feasible sessions to database
    saved_sessions = []
    for s_dict in result["schedules"]:
        sched = Schedule(
            experiment_id=s_dict["experiment_id"],
            batch_id=s_dict["batch_id"],
            laboratory_id=s_dict["laboratory_id"],
            faculty_id=s_dict["faculty_id"],
            session_number=s_dict["session_number"],
            date=s_dict["date"],
            start_time=s_dict["start_time"],
            end_time=s_dict["end_time"],
            student_capacity=s_dict["student_capacity"],
            expected_students=s_dict["expected_students"],
            remaining_learning_gap=s_dict["remaining_learning_gap"],
            status="Scheduled"
        )
        db.add(sched)
        saved_sessions.append(s_dict)

    db.commit()
    result["schedules"] = saved_sessions
    return result

@router.post("/auto-allocate")
def auto_allocate_curriculum(
    payload: AutoAllocateRequest,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """
    Automated cohort curriculum allocation across multiple batches and laboratories.
    Guarantees zero double booking, respects laboratory operating hours, and honors shared equipment limits.
    """
    return auto_allocate_cohort_curriculum(
        db=db,
        batch_ids=payload.batch_ids,
        start_date=payload.start_date,
        clear_existing=payload.clear_existing or False
    )

@router.get("/smart-recommendations")
def get_smart_lab_recommendations(
    experiment_id: int,
    batch_id: int,
    current_user: User = Depends(require_all_authenticated),
    db: Session = Depends(get_db)
):
    """
    Evaluates and ranks candidate laboratories based on mandatory equipment,
    functional unit quantities, capacity fit, and existing schedule contention.
    """
    return evaluate_smart_laboratory_allocations(
        db=db,
        experiment_id=experiment_id,
        batch_id=batch_id
    )

@router.post("/approve-allocation")
def approve_laboratory_allocation(
    payload: ApproveAllocationRequest,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """
    Administrator approves a recommended or alternative laboratory allocation.
    Validates feasibility, updates curriculum mapping, and generates schedule sessions.
    Strictly rejects infeasible allocations.
    """
    eval_result = evaluate_smart_laboratory_allocations(
        db=db,
        experiment_id=payload.experiment_id,
        batch_id=payload.batch_id
    )
    
    target_lab_eval = None
    all_evals = []
    if eval_result.get("best_recommendation"):
        all_evals.append(eval_result["best_recommendation"])
    all_evals.extend(eval_result.get("alternative_options", []))
    all_evals.extend(eval_result.get("rejected_laboratories", []))

    for e in all_evals:
        if e["laboratory_id"] == payload.laboratory_id:
            target_lab_eval = e
            break

    if not target_lab_eval:
        raise HTTPException(status_code=404, detail="Selected laboratory not found for this department.")

    if not target_lab_eval["is_feasible"]:
        reasons = "; ".join(target_lab_eval["rejection_reasons"])
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot approve allocation: Laboratory is infeasible for this experiment ({reasons})."
        )

    # 1. Update experiment's active laboratory if needed
    exp = db.query(Experiment).filter(Experiment.id == payload.experiment_id).first()
    if exp:
        exp.laboratory_id = payload.laboratory_id

    # 2. Ensure batch is associated with this experiment
    existing_link = db.query(BatchExperiment).filter(
        BatchExperiment.batch_id == payload.batch_id,
        BatchExperiment.experiment_id == payload.experiment_id
    ).first()
    if not existing_link:
        db.add(BatchExperiment(batch_id=payload.batch_id, experiment_id=payload.experiment_id))
    db.commit()

    # 3. Generate zero-conflict schedule sessions
    sched_res = generate_optimized_schedule(
        db=db,
        experiment_id=payload.experiment_id,
        batch_id=payload.batch_id,
        start_date=payload.start_date
    )

    if not sched_res.get("success"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=sched_res.get("message", "Unable to generate schedule for approved laboratory.")
        )

    # 4. Save generated sessions to database
    saved_sessions = []
    for s_dict in sched_res["schedules"]:
        sched = Schedule(
            experiment_id=s_dict["experiment_id"],
            batch_id=s_dict["batch_id"],
            laboratory_id=payload.laboratory_id,
            faculty_id=s_dict["faculty_id"],
            session_number=s_dict["session_number"],
            date=s_dict["date"],
            start_time=s_dict["start_time"],
            end_time=s_dict["end_time"],
            student_capacity=s_dict["student_capacity"],
            expected_students=s_dict["expected_students"],
            remaining_learning_gap=s_dict["remaining_learning_gap"],
            status="Scheduled"
        )
        db.add(sched)
        saved_sessions.append(s_dict)

    db.commit()

    return {
        "success": True,
        "message": f"Successfully approved allocation of '{eval_result['experiment_name']}' to '{target_lab_eval['laboratory_name']}'.",
        "laboratory_id": payload.laboratory_id,
        "laboratory_name": target_lab_eval["laboratory_name"],
        "suitability_score": target_lab_eval["suitability_score"],
        "sessions_scheduled": len(saved_sessions),
        "schedules": saved_sessions
    }

@router.delete("/clear")
def clear_all_schedules(
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    db.query(Schedule).delete()
    db.commit()
    return {"message": "All scheduled sessions cleared successfully"}
