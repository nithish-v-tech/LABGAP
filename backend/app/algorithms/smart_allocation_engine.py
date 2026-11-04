import math
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from app.database.models import (
    Laboratory, Experiment, StudentBatch, Equipment, ExperimentEquipment,
    Schedule, CompletionRecord, Student, Faculty
)
from app.algorithms.capacity_engine import calculate_experiment_capacity

def evaluate_smart_laboratory_allocations(
    db: Session,
    experiment_id: int,
    batch_id: int
) -> Dict[str, Any]:
    """
    Evaluates and ranks all laboratories in the department for conducting
    a specific experiment with a given student batch.
    Uses transparent, explainable rule-based scoring (0-100).
    """
    experiment = db.query(Experiment).filter(Experiment.id == experiment_id).first()
    batch = db.query(StudentBatch).filter(StudentBatch.id == batch_id).first()

    if not experiment:
        return {"error": "Experiment not found", "recommendations": []}
    if not batch:
        return {"error": "Student batch not found", "recommendations": []}

    batch_size = batch.number_of_students or 20
    students_per_unit = experiment.students_per_unit or 2
    min_safe_batch = experiment.min_safe_batch_size or 4
    max_safe_batch = experiment.max_safe_batch_size or 30

    # Query all laboratories in department (or institution)
    dept_id = experiment.laboratory.department_id if experiment.laboratory else batch.department_id
    laboratories = db.query(Laboratory).filter(Laboratory.department_id == dept_id).all()
    if not laboratories:
        laboratories = db.query(Laboratory).all()

    # Get experiment requirements
    requirements = db.query(ExperimentEquipment).filter(
        ExperimentEquipment.experiment_id == experiment.id
    ).all()

    evaluations = []

    for lab in laboratories:
        rejection_reasons = []
        positive_factors = []
        is_feasible = True

        # 1. Capacity Check
        lab_cap = lab.max_student_capacity or 30
        if lab_cap < min_safe_batch:
            is_feasible = False
            rejection_reasons.append(f"Laboratory capacity ({lab_cap}) is below minimum safe batch size ({min_safe_batch}).")
        elif lab_cap < batch_size:
            positive_factors.append(f"Requires rotation splitting (Lab capacity {lab_cap} < Batch size {batch_size}).")

        # 2. Equipment Availability in this Laboratory
        lab_equipment = db.query(Equipment).filter(Equipment.laboratory_id == lab.id).all()
        eq_by_name = {e.name.lower(): e for e in lab_equipment}
        eq_by_code = {e.equipment_code.lower(): e for e in lab_equipment}

        station_counts = []
        equipment_statuses = []
        total_shortage = 0

        for req in requirements:
            req_eq = db.query(Equipment).filter(Equipment.id == req.equipment_id).first()
            if not req_eq:
                continue

            # Check if this lab has matching equipment (by ID, code, or name)
            matching_eq = None
            if req_eq.laboratory_id == lab.id:
                matching_eq = req_eq
            elif req_eq.equipment_code.lower() in eq_by_code:
                matching_eq = eq_by_code[req_eq.equipment_code.lower()]
            elif req_eq.name.lower() in eq_by_name:
                matching_eq = eq_by_name[req_eq.name.lower()]

            if not matching_eq:
                is_feasible = False
                rejection_reasons.append(f"Missing mandatory equipment: '{req_eq.name}' not installed in this laboratory.")
                equipment_statuses.append({
                    "equipment_name": req_eq.name,
                    "functional_available": 0,
                    "required_per_station": req.quantity_required,
                    "status": "Missing"
                })
                station_counts.append(0)
            else:
                func_qty = matching_eq.functional_quantity
                stations = math.floor(func_qty / req.quantity_required) if req.quantity_required > 0 else 0
                station_counts.append(stations)

                if stations == 0 and req.is_critical:
                    is_feasible = False
                    rejection_reasons.append(
                        f"Zero functional units of critical equipment '{matching_eq.name}' "
                        f"({matching_eq.damaged_quantity} damaged, {matching_eq.under_maintenance_quantity} in maintenance)."
                    )

                needed_for_batch = math.ceil(batch_size / students_per_unit) * req.quantity_required
                if func_qty < needed_for_batch:
                    total_shortage += (needed_for_batch - func_qty)

                equipment_statuses.append({
                    "equipment_name": matching_eq.name,
                    "functional_available": func_qty,
                    "required_per_station": req.quantity_required,
                    "damaged": matching_eq.damaged_quantity,
                    "status": "Operational" if stations > 0 else "Bottleneck"
                })

        active_stations = min(station_counts) if station_counts else 0
        safe_practical_capacity = min(active_stations * students_per_unit, lab_cap, max_safe_batch)

        if safe_practical_capacity <= 0:
            is_feasible = False
            if not rejection_reasons:
                rejection_reasons.append("No active practical stations can be formed with functional equipment.")

        # 3. Schedule & Contention Check
        existing_schedules = db.query(Schedule).filter(
            Schedule.laboratory_id == lab.id,
            Schedule.status == "Scheduled"
        ).count()

        # 4. Transparent Scoring Algorithm (0 - 100)
        # Base components:
        # A. Equipment Health Score (max 50 pts)
        if not is_feasible:
            score = 0
        else:
            eq_ratio = min(1.0, active_stations / max(1, math.ceil(batch_size / students_per_unit)))
            eq_score = eq_ratio * 50

            # B. Capacity Fit Score (max 30 pts)
            cap_ratio = min(1.0, safe_practical_capacity / batch_size)
            cap_score = cap_ratio * 30

            # C. Availability & Contention Score (max 20 pts)
            contention_penalty = min(15, existing_schedules * 2)
            availability_score = max(5, 20 - contention_penalty)

            score = round(eq_score + cap_score + availability_score, 1)

            if lab.id == experiment.laboratory_id:
                score = min(100.0, score + 5.0)  # Slight bonus for primary assigned lab
                positive_factors.append("Designated primary curriculum laboratory.")

            positive_factors.append(f"{active_stations} active stations ({safe_practical_capacity} safe capacity/session).")
            if existing_schedules == 0:
                positive_factors.append("Zero current scheduling contention.")
            else:
                positive_factors.append(f"{existing_schedules} existing scheduled session(s).")

        evaluations.append({
            "laboratory_id": lab.id,
            "laboratory_code": lab.code,
            "laboratory_name": lab.name,
            "location": lab.location,
            "operating_hours": f"{lab.open_time or '09:00'} - {lab.close_time or '17:00'}",
            "laboratory_capacity": lab_cap,
            "is_feasible": is_feasible,
            "suitability_score": score,
            "active_stations": active_stations,
            "safe_practical_capacity": safe_practical_capacity,
            "batch_size": batch_size,
            "equipment_shortage_units": total_shortage,
            "existing_bookings_count": existing_schedules,
            "positive_factors": positive_factors,
            "rejection_reasons": rejection_reasons,
            "equipment_breakdown": equipment_statuses
        })

    # Sort evaluations: feasible first, then by highest score descending
    evaluations.sort(key=lambda x: (x["is_feasible"], x["suitability_score"]), reverse=True)

    # Assign ranks
    best_recommendation = None
    alternative_options = []
    rejected_laboratories = []

    for idx, e in enumerate(evaluations):
        e["rank"] = idx + 1
        if e["is_feasible"] and best_recommendation is None:
            best_recommendation = e
        elif e["is_feasible"]:
            alternative_options.append(e)
        else:
            rejected_laboratories.append(e)

    return {
        "experiment_id": experiment.id,
        "experiment_code": experiment.experiment_code,
        "experiment_name": experiment.name,
        "batch_id": batch.id,
        "batch_code": batch.batch_code,
        "batch_name": batch.batch_name,
        "batch_size": batch_size,
        "has_feasible_lab": best_recommendation is not None,
        "best_recommendation": best_recommendation,
        "alternative_options": alternative_options,
        "rejected_laboratories": rejected_laboratories,
        "total_evaluated": len(evaluations)
    }
