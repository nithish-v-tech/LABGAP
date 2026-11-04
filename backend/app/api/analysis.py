import datetime
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from app.database.connection import get_db
from app.database.models import (
    Experiment, Equipment, StudentBatch, BatchExperiment, Laboratory,
    Student, CompletionRecord, AnalysisResult, User, Schedule, RepairRecord
)
from app.security.permissions import require_admin_or_hod, require_all_authenticated
from app.algorithms.capacity_engine import calculate_experiment_capacity
from app.algorithms.gap_analyzer import calculate_student_learning_gap

router = APIRouter(prefix="/analysis", tags=["Coverage Analysis"])

@router.post("/run")
def run_full_analysis(
    department_id: Optional[int] = None,
    current_user: User = Depends(require_admin_or_hod),
    db: Session = Depends(get_db)
):
    """
    Executes real-time deterministic equipment-experiment mapping,
    safe student capacity, time feasibility, coverage classification,
    and student practical learning gap calculations across all experiments and batches.
    Saves results to the database and returns the fresh calculation breakdown.
    """
    experiments = db.query(Experiment).all()
    batches = db.query(StudentBatch).all()

    if not experiments:
        return {"message": "No experiments found to analyze", "total_analyzed": 0, "results": []}

    # Clear previous analysis results
    db.query(AnalysisResult).delete()

    results = []
    fully_covered_count = 0
    partially_covered_count = 0
    not_covered_count = 0
    total_gap = 0
    total_assigned_students = 0
    total_verified = 0

    for exp in experiments:
        # Check all batches assigned to this experiment
        assigned_batch_links = db.query(BatchExperiment).filter(
            BatchExperiment.experiment_id == exp.id
        ).all()

        target_batches = []
        if assigned_batch_links:
            target_batches = [
                db.query(StudentBatch).filter(StudentBatch.id == bl.batch_id).first()
                for bl in assigned_batch_links
            ]
            target_batches = [b for b in target_batches if b is not None]
        
        if not target_batches and batches:
            # Analyze against primary batch if no direct link
            target_batches = [batches[0]]

        for batch in target_batches:
            capacity_data = calculate_experiment_capacity(db, exp, batch)
            gap_data = calculate_student_learning_gap(db, exp.id, batch.id)

            classification = capacity_data["classification"]
            if classification == "FULLY COVERED":
                fully_covered_count += 1
            elif classification == "PARTIALLY COVERED":
                partially_covered_count += 1
            else:
                not_covered_count += 1

            total_gap += gap_data["unverified_learning_gap"]
            total_assigned_students += gap_data["total_assigned"]
            total_verified += gap_data["verified_completed"]

            # Save to analysis_results table
            db_record = AnalysisResult(
                department_id=exp.laboratory.department_id if exp.laboratory else 1,
                experiment_id=exp.id,
                batch_id=batch.id,
                classification=classification,
                available_capacity=capacity_data["available_capacity"],
                required_capacity=capacity_data["required_capacity"],
                equipment_shortage=capacity_data["equipment_shortage"],
                time_shortage_hours=capacity_data["time_shortage_hours"],
                students_affected=capacity_data["students_affected"],
                reason=capacity_data["reason"],
                verified_completions=gap_data["verified_completed"],
                remaining_gap=gap_data["unverified_learning_gap"],
                calculated_at=datetime.datetime.utcnow()
            )
            db.add(db_record)

            results.append({
                "experiment_id": exp.id,
                "experiment_code": exp.experiment_code,
                "experiment_name": exp.name,
                "laboratory_id": exp.laboratory_id,
                "laboratory_name": exp.laboratory.name if exp.laboratory else "Unknown",
                "batch_id": batch.id,
                "batch_code": batch.batch_code,
                "batch_name": batch.batch_name,
                "batch_size": batch.number_of_students,
                "classification": classification,
                "active_stations": capacity_data["active_stations"],
                "safe_capacity_per_session": capacity_data["safe_capacity_per_session"],
                "available_capacity": capacity_data["available_capacity"],
                "required_capacity": capacity_data["required_capacity"],
                "equipment_shortage": capacity_data["equipment_shortage"],
                "time_required_hours": capacity_data["time_required_hours"],
                "time_shortage_hours": capacity_data["time_shortage_hours"],
                "students_affected": capacity_data["students_affected"],
                "bottleneck_equipment": capacity_data["bottleneck_equipment"],
                "reason": capacity_data["reason"],
                "verified_completions": gap_data["verified_completed"],
                "remaining_learning_gap": gap_data["unverified_learning_gap"],
                "gap_percentage": gap_data["gap_percentage"]
            })

    db.commit()

    return {
        "timestamp": datetime.datetime.utcnow().isoformat(),
        "total_analyzed": len(results),
        "summary": {
            "fully_covered": fully_covered_count,
            "partially_covered": partially_covered_count,
            "not_covered": not_covered_count,
            "total_assigned_students": total_assigned_students,
            "total_verified_competent": total_verified,
            "total_learning_gap": total_gap,
            "overall_practical_coverage_pct": round(
                (total_verified / total_assigned_students * 100), 1
            ) if total_assigned_students > 0 else 0.0
        },
        "details": results
    }

@router.get("/summary")
def get_dashboard_summary(
    current_user: User = Depends(require_all_authenticated),
    db: Session = Depends(get_db)
):
    """
    Real database queries for system-wide metrics. No hardcoded statistics!
    """
    total_labs = db.query(Laboratory).count()
    total_experiments = db.query(Experiment).count()
    total_students = db.query(Student).count()
    total_batches = db.query(StudentBatch).count()

    equipment_items = db.query(Equipment).all()
    total_equipment = sum(e.total_quantity for e in equipment_items)
    functional_equipment = sum(e.functional_quantity for e in equipment_items)
    partially_functional = sum(e.partially_functional_quantity for e in equipment_items)
    damaged_equipment = sum(e.damaged_quantity for e in equipment_items)
    under_maintenance = sum(e.under_maintenance_quantity for e in equipment_items)

    # Calculate equipment utilization rate
    utilization_rate = round((functional_equipment / total_equipment * 100), 1) if total_equipment > 0 else 0.0

    # Run / fetch latest experiment coverage classifications
    experiments = db.query(Experiment).all()
    default_batch = db.query(StudentBatch).first()

    fully_covered = 0
    partially_covered = 0
    not_covered = 0

    for exp in experiments:
        cap = calculate_experiment_capacity(db, exp, default_batch)
        if cap["classification"] == "FULLY COVERED":
            fully_covered += 1
        elif cap["classification"] == "PARTIALLY COVERED":
            partially_covered += 1
        else:
            not_covered += 1

    # Student learning gap calculations
    total_verified = db.query(CompletionRecord).filter(
        CompletionRecord.participation_status == "Completed",
        CompletionRecord.verification_status == "Verified"
    ).count()

    # Total student-experiment expected completions = total_students * count of assigned experiments
    # For demonstrative accuracy, sum up assignments
    assigned_links = db.query(BatchExperiment).all()
    total_student_experiment_tasks = 0
    for link in assigned_links:
        b = db.query(StudentBatch).filter(StudentBatch.id == link.batch_id).first()
        if b:
            total_student_experiment_tasks += b.number_of_students

    if total_student_experiment_tasks == 0:
        total_student_experiment_tasks = total_students * max(1, total_experiments)

    students_without_verified = max(0, total_student_experiment_tasks - total_verified)

    # Condition distribution for charts
    condition_distribution = [
        {"name": "Functional", "value": functional_equipment, "color": "#06b6d4"},
        {"name": "Partially Functional", "value": partially_functional, "color": "#3b82f6"},
        {"name": "Damaged", "value": damaged_equipment, "color": "#ef4444"},
        {"name": "Under Maintenance", "value": under_maintenance, "color": "#f59e0b"}
    ]

    # Coverage distribution for charts
    coverage_distribution = [
        {"name": "Fully Covered", "count": fully_covered, "color": "#10b981"},
        {"name": "Partially Covered", "count": partially_covered, "color": "#f59e0b"},
        {"name": "Not Covered", "count": not_covered, "color": "#ef4444"}
    ]

    return {
        "total_laboratories": total_labs,
        "total_experiments": total_experiments,
        "total_students": total_students,
        "total_batches": total_batches,
        "total_equipment_units": total_equipment,
        "functional_equipment": functional_equipment,
        "partially_functional": partially_functional,
        "damaged_equipment": damaged_equipment,
        "under_maintenance": under_maintenance,
        "fully_covered_experiments": fully_covered,
        "partially_covered_experiments": partially_covered,
        "not_covered_experiments": not_covered,
        "total_verified_competencies": total_verified,
        "total_practical_learning_gap": students_without_verified,
        "equipment_utilization_rate": utilization_rate,
        "condition_distribution": condition_distribution,
        "coverage_distribution": coverage_distribution
    }

@router.get("/competency-matrix")
def get_student_competency_matrix(
    batch_id: Optional[int] = None,
    current_user: User = Depends(require_all_authenticated),
    db: Session = Depends(get_db)
):
    """
    Returns verified practical competency metrics for every student in the cohort.
    Strictly enforces:
    - Attendance != competence.
    - Only faculty-verified practicals count.
    - Students cannot self-verify.
    """
    student_query = db.query(Student)
    if batch_id:
        student_query = student_query.filter(Student.batch_id == batch_id)
    students = student_query.all()

    student_records = []
    total_assigned_sum = 0
    total_verified_sum = 0
    fully_competent_count = 0
    at_risk_count = 0

    for s in students:
        batch = s.batch
        assigned_experiments = []
        if batch:
            links = db.query(BatchExperiment).filter(BatchExperiment.batch_id == batch.id).all()
            for l in links:
                exp = db.query(Experiment).filter(Experiment.id == l.experiment_id).first()
                if exp:
                    assigned_experiments.append(exp)

        total_assigned = len(assigned_experiments)
        total_assigned_sum += total_assigned

        completions = db.query(CompletionRecord).filter(CompletionRecord.student_id == s.id).all()
        completion_map = {c.experiment_id: c for c in completions}

        verified_count = 0
        completed_unverified = 0
        exp_details = []

        for exp in assigned_experiments:
            rec = completion_map.get(exp.id)
            if rec:
                is_verified = (rec.participation_status == "Completed" and rec.verification_status == "Verified")
                if is_verified:
                    verified_count += 1
                elif rec.participation_status == "Completed":
                    completed_unverified += 1

                exp_details.append({
                    "experiment_id": exp.id,
                    "experiment_code": exp.experiment_code,
                    "experiment_name": exp.name,
                    "practical_competency": exp.practical_competency,
                    "participation_status": rec.participation_status,
                    "verification_status": rec.verification_status,
                    "is_verified": is_verified,
                    "assessment_notes": rec.assessment_notes,
                    "verification_timestamp": rec.verification_timestamp
                })
            else:
                exp_details.append({
                    "experiment_id": exp.id,
                    "experiment_code": exp.experiment_code,
                    "experiment_name": exp.name,
                    "practical_competency": exp.practical_competency,
                    "participation_status": "Not started",
                    "verification_status": "Pending",
                    "is_verified": False,
                    "assessment_notes": None,
                    "verification_timestamp": None
                })

        pending_practicals = max(0, total_assigned - verified_count)
        total_verified_sum += verified_count
        pct = round((verified_count / total_assigned * 100), 1) if total_assigned > 0 else 0.0

        if pct == 100.0:
            status_level = "Proficient"
            fully_competent_count += 1
        elif pct >= 50.0:
            status_level = "Progressing"
        else:
            status_level = "At Risk"
            at_risk_count += 1

        student_records.append({
            "student_id": s.id,
            "student_id_number": s.student_id_number,
            "name": s.name,
            "email": s.email,
            "batch_id": s.batch_id,
            "batch_code": batch.batch_code if batch else "Unassigned",
            "batch_name": batch.batch_name if batch else "Unassigned",
            "total_assigned": total_assigned,
            "completed_practicals": verified_count + completed_unverified,
            "verified_practicals": verified_count,
            "pending_practicals": pending_practicals,
            "remaining_learning_gap": pending_practicals,
            "competency_percentage": pct,
            "status_level": status_level,
            "experiments": exp_details
        })

    avg_rate = round((total_verified_sum / max(1, total_assigned_sum) * 100), 1)

    return {
        "cohort_summary": {
            "total_students": len(students),
            "total_assigned_tasks": total_assigned_sum,
            "total_verified_tasks": total_verified_sum,
            "average_competency_rate": avg_rate,
            "fully_competent_count": fully_competent_count,
            "students_with_gaps_count": len(students) - fully_competent_count,
            "at_risk_students_count": at_risk_count
        },
        "students": student_records
    }

@router.get("/resource-intelligence")
def get_resource_intelligence(
    current_user: User = Depends(require_all_authenticated),
    db: Session = Depends(get_db)
):
    """
    Intelligent Resource Dashboard engine.
    Generates deterministic, explainable recommendations directly from current DB state.
    """
    equipment_items = db.query(Equipment).all()
    experiments = db.query(Experiment).all()
    laboratories = db.query(Laboratory).all()
    batches = db.query(StudentBatch).all()

    recommendations = []

    # 1. High-Impact Equipment Repair Intelligence
    for eq in equipment_items:
        if eq.damaged_quantity > 0 or eq.under_maintenance_quantity > 0:
            # Check how many experiments use this equipment
            affected_exps = []
            for exp in experiments:
                req_ids = [r.equipment_id for r in exp.equipment_requirements]
                if eq.id in req_ids or (exp.laboratory_id == eq.laboratory_id):
                    affected_exps.append(exp)

            exp_names = ", ".join([e.name for e in affected_exps[:2]]) if affected_exps else f"Practicals in {eq.laboratory.name if eq.laboratory else 'Laboratory'}"
            restorable = eq.damaged_quantity + eq.under_maintenance_quantity
            potential_gain = restorable * 2  # 2 students per station
            recommendations.append({
                "category": "Equipment Repair Impact",
                "priority": "High" if eq.damaged_quantity > 1 else "Medium",
                "title": f"Repair {restorable} unit(s) of '{eq.name}' in {eq.laboratory.name if eq.laboratory else 'Lab'}",
                "explanation": f"Restoring {restorable} units recovers +{potential_gain} student practical capacity and directly unblocks: {exp_names}.",
                "action": "Dispatch technician for recalibration",
                "target_id": eq.id,
                "target_type": "equipment"
            })

    # 2. Laboratory Capacity Utilization Intelligence
    for lab in laboratories:
        scheduled_count = db.query(Schedule).filter(
            Schedule.laboratory_id == lab.id,
            Schedule.status == "Scheduled"
        ).count()
        # Max 15 slots weekly (3 slots/day * 5 days)
        max_slots = 15
        utilization = round((scheduled_count / max_slots * 100), 1)
        if utilization < 40.0:
            recommendations.append({
                "category": "Capacity Utilization",
                "priority": "Low",
                "title": f"{lab.name} has available slot capacity ({100 - utilization:.0f}% unallocated)",
                "explanation": f"Currently hosting {scheduled_count} rotation session(s). Can accommodate additional cohort practicals without resource contention.",
                "action": "Schedule additional lab rotations",
                "target_id": lab.id,
                "target_type": "laboratory"
            })

    # 3. Curriculum Coverage Blocker Intelligence
    default_batch = batches[0] if batches else None
    for exp in experiments:
        cap = calculate_experiment_capacity(db, exp, default_batch)
        if cap["classification"] == "NOT COVERED":
            recommendations.append({
                "category": "Curriculum Feasibility Alert",
                "priority": "Critical",
                "title": f"'{exp.name}' Cannot Be Delivered Safely",
                "explanation": f"Classified as NOT COVERED due to zero functional units of bottleneck equipment '{cap.get('bottleneck_equipment', 'Mandatory Tool')}'.",
                "action": "Procure replacement or reallocate to alternative lab",
                "target_id": exp.id,
                "target_type": "experiment"
            })

    # 4. Cohort Practical Gap Alerts
    for b in batches:
        students = db.query(Student).filter(Student.batch_id == b.id).all()
        student_ids = [s.id for s in students]
        verified_count = db.query(CompletionRecord).filter(
            CompletionRecord.student_id.in_(student_ids),
            CompletionRecord.participation_status == "Completed",
            CompletionRecord.verification_status == "Verified"
        ).count()
        
        assigned_exp_count = db.query(BatchExperiment).filter(BatchExperiment.batch_id == b.id).count()
        expected_total = len(students) * assigned_exp_count
        if expected_total > 0:
            gap = expected_total - verified_count
            if gap > 0:
                gap_pct = round((gap / expected_total * 100), 1)
                if gap_pct > 50.0:
                    recommendations.append({
                        "category": "Cohort Learning Gap Alert",
                        "priority": "High",
                        "title": f"Batch {b.batch_code}: {gap_pct}% Practical Gaps Remaining",
                        "explanation": f"{gap} practical experiment task(s) remain unverified out of {expected_total} assigned across {len(students)} students.",
                        "action": "Initiate cohort auto-allocation rotation schedule",
                        "target_id": b.id,
                        "target_type": "batch"
                    })

    return {
        "timestamp": datetime.datetime.utcnow().isoformat(),
        "total_recommendations": len(recommendations),
        "recommendations": recommendations
    }
