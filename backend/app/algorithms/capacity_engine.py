import math
from typing import Dict, Any, List
from sqlalchemy.orm import Session
from app.database.models import Experiment, Equipment, StudentBatch, ExperimentEquipment, Laboratory

def calculate_experiment_capacity(
    db: Session,
    experiment: Experiment,
    batch: StudentBatch,
    lab_weekly_hours: float = 8.0
) -> Dict[str, Any]:
    """
    Deterministic rule-based capacity calculation and coverage classification.
    """
    batch_size = batch.number_of_students if batch else 30
    students_per_unit = experiment.students_per_unit or 2
    min_safe_batch = experiment.min_safe_batch_size or 4
    max_safe_batch = experiment.max_safe_batch_size or 30
    duration_hours = experiment.duration_hours or 2.0

    # Read equipment requirements
    requirements = db.query(ExperimentEquipment).filter(
        ExperimentEquipment.experiment_id == experiment.id
    ).all()

    if not requirements:
        # Fallback to laboratory's general equipment or default calculation
        active_stations = 5
        bottleneck_equipment = None
        min_available = 5
        shortage = 0
    else:
        station_capacities = []
        shortage = 0
        bottleneck_equipment = None
        min_available = 999999

        for req in requirements:
            eq = db.query(Equipment).filter(Equipment.id == req.equipment_id).first()
            if not eq:
                station_capacities.append(0)
                shortage += req.quantity_required
                bottleneck_equipment = "Missing Equipment Reference"
                continue

            # Functional equipment availability:
            # Damaged and under maintenance are NOT counted
            functional_avail = eq.functional_quantity
            # If approved, partially functional could add limited support, but strictly count verified functional
            stations_for_this_eq = math.floor(functional_avail / req.quantity_required) if req.quantity_required > 0 else 0
            station_capacities.append(stations_for_this_eq)

            if stations_for_this_eq < min_available:
                min_available = stations_for_this_eq
                bottleneck_equipment = eq.name
                # Calculate equipment shortage needed to support full single batch session
                needed_units = math.ceil(batch_size / students_per_unit) * req.quantity_required
                if functional_avail < needed_units:
                    shortage = max(shortage, needed_units - functional_avail)

        active_stations = min(station_capacities) if station_capacities else 0

    # Calculate safe student capacity per session
    raw_capacity_per_session = active_stations * students_per_unit
    safe_capacity_per_session = min(raw_capacity_per_session, max_safe_batch)

    # Determine feasibility
    if safe_capacity_per_session <= 0 or active_stations == 0:
        classification = "NOT COVERED"
        required_sessions = 0
        time_required_hours = 0.0
        time_shortage_hours = 0.0
        students_affected = batch_size
        available_capacity = 0
        reason = (
            f"Zero functional units of critical equipment ({bottleneck_equipment or 'Required Equipment'}) "
            f"available in {experiment.laboratory.name if experiment.laboratory else 'Laboratory'}. "
            f"No safe practical session can be conducted."
        )
    else:
        required_sessions = math.ceil(batch_size / safe_capacity_per_session)
        time_required_hours = required_sessions * duration_hours
        
        # Max sessions laboratory can host in a weekly cycle
        max_possible_sessions = math.floor(lab_weekly_hours / duration_hours)
        total_accommodated_students = max_possible_sessions * safe_capacity_per_session

        if total_accommodated_students >= batch_size and time_required_hours <= lab_weekly_hours:
            classification = "FULLY COVERED"
            available_capacity = min(total_accommodated_students, batch_size)
            time_shortage_hours = 0.0
            students_affected = 0
            reason = (
                f"Sufficient functional equipment ({active_stations} active stations, {safe_capacity_per_session} "
                f"students/session). Full batch of {batch_size} students accommodated across {required_sessions} "
                f"rotation session(s) requiring {time_required_hours:.1f} hours out of {lab_weekly_hours:.1f} available hours."
            )
        else:
            classification = "PARTIALLY COVERED"
            available_capacity = min(total_accommodated_students, batch_size)
            time_shortage_hours = max(0.0, time_required_hours - lab_weekly_hours)
            students_affected = max(0, batch_size - total_accommodated_students)
            reason = (
                f"Equipment constraint on {bottleneck_equipment} limits session capacity to {safe_capacity_per_session} "
                f"students ({active_stations} stations). Complete batch delivery requires {required_sessions} sessions "
                f"({time_required_hours:.1f} hours), creating a deficit against {lab_weekly_hours:.1f} available laboratory hours. "
                f"{students_affected} student(s) cannot receive practical rotation without extra sessions or repairs."
            )

    return {
        "experiment_id": experiment.id,
        "experiment_code": experiment.experiment_code,
        "experiment_name": experiment.name,
        "batch_id": batch.id if batch else None,
        "batch_code": batch.batch_code if batch else "N/A",
        "batch_size": batch_size,
        "classification": classification,
        "active_stations": active_stations,
        "safe_capacity_per_session": safe_capacity_per_session,
        "available_capacity": available_capacity,
        "required_capacity": batch_size,
        "equipment_shortage": shortage,
        "required_sessions": required_sessions,
        "time_required_hours": time_required_hours,
        "time_shortage_hours": time_shortage_hours,
        "students_affected": students_affected,
        "bottleneck_equipment": bottleneck_equipment,
        "reason": reason
    }
