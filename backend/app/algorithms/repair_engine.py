from typing import List, Dict, Any
from sqlalchemy.orm import Session
from app.database.models import Equipment, ExperimentEquipment, Experiment, BatchExperiment, StudentBatch, RepairRecord

def evaluate_equipment_repairs(db: Session) -> List[Dict[str, Any]]:
    """
    Ranks equipment repair priorities based on practical learning gap impact,
    number of blocked experiments, student reach, and potential capacity gain.
    """
    # Query all equipment with non-zero damaged or under maintenance quantities
    problematic_equipment = db.query(Equipment).filter(
        (Equipment.damaged_quantity > 0) | 
        (Equipment.under_maintenance_quantity > 0) | 
        (Equipment.partially_functional_quantity > 0)
    ).all()

    recommendations = []

    for eq in problematic_equipment:
        # Find all experiments linked to this equipment
        exp_links = db.query(ExperimentEquipment).filter(
            ExperimentEquipment.equipment_id == eq.id
        ).all()

        linked_experiments = []
        total_students_impacted = 0
        blocked_experiments_count = 0

        for link in exp_links:
            exp = db.query(Experiment).filter(Experiment.id == link.experiment_id).first()
            if not exp:
                continue

            # Find batches assigned to this experiment
            batch_links = db.query(BatchExperiment).filter(
                BatchExperiment.experiment_id == exp.id
            ).all()

            exp_students = 0
            for bl in batch_links:
                batch = db.query(StudentBatch).filter(StudentBatch.id == bl.batch_id).first()
                if batch:
                    exp_students += batch.number_of_students

            total_students_impacted += exp_students

            # If functional quantity is zero or less than required quantity
            if eq.functional_quantity < link.quantity_required:
                blocked_experiments_count += 1

            linked_experiments.append({
                "experiment_id": exp.id,
                "experiment_code": exp.experiment_code,
                "name": exp.name,
                "students_per_unit": exp.students_per_unit,
                "batch_students": exp_students
            })

        # Calculate potential capacity gain
        repairable_units = eq.damaged_quantity + eq.under_maintenance_quantity
        avg_students_per_unit = 2
        if linked_experiments:
            avg_students_per_unit = max(
                exp["students_per_unit"] for exp in linked_experiments
            )
        potential_capacity_gain = repairable_units * avg_students_per_unit

        # Determine Priority Level
        if blocked_experiments_count > 0 and total_students_impacted >= 30:
            priority = "Critical"
            reason = (
                f"Critical blocker: {eq.damaged_quantity} damaged unit(s) completely halt "
                f"{blocked_experiments_count} experiment(s) with {total_students_impacted} assigned student(s). "
                f"Zero practical delivery possible until repaired."
            )
            suggested_action = "Immediate vendor dispatch or component replacement. High institutional priority."
        elif blocked_experiments_count > 0 or (eq.damaged_quantity >= 3 and total_students_impacted > 20):
            priority = "High"
            reason = (
                f"Significant capacity deficit: Restricts practical batch throughput across "
                f"{len(linked_experiments)} experiment(s). Repairing {repairable_units} unit(s) will add "
                f"{potential_capacity_gain} student slots per session."
            )
            suggested_action = "Schedule technician maintenance within 48 hours to restore rotation throughput."
        elif repairable_units > 0:
            priority = "Medium"
            reason = (
                f"Moderate shortage: Reduces redundancy for {len(linked_experiments)} experiment(s). "
                f"Current functional units satisfy reduced rotation schedules but increase wear."
            )
            suggested_action = "Queue for routine batch maintenance during upcoming laboratory recess."
        else:
            priority = "Low"
            reason = (
                f"Minor wear: {eq.partially_functional_quantity} partially functional unit(s). "
                f"Non-critical for primary learning outcomes."
            )
            suggested_action = "Monitor condition and perform sensor recalibration during standard checkup."

        expected_improvement = (
            f"Restoring {repairable_units} unit(s) provides +{potential_capacity_gain} safe student seats "
            f"per session and eliminates bottlenecks across {len(linked_experiments)} syllabus experiment(s)."
        )

        condition_summary = []
        if eq.damaged_quantity > 0:
            condition_summary.append(f"{eq.damaged_quantity} Damaged")
        if eq.under_maintenance_quantity > 0:
            condition_summary.append(f"{eq.under_maintenance_quantity} In Maintenance")
        if eq.partially_functional_quantity > 0:
            condition_summary.append(f"{eq.partially_functional_quantity} Partially Functional")
        condition_str = ", ".join(condition_summary) if condition_summary else "Functional"

        recommendations.append({
            "equipment_id": eq.id,
            "equipment_code": eq.equipment_code,
            "equipment_name": eq.name,
            "laboratory_id": eq.laboratory_id,
            "laboratory_name": eq.laboratory.name if eq.laboratory else "Unknown",
            "priority": priority,
            "current_condition": condition_str,
            "total_quantity": eq.total_quantity,
            "functional_quantity": eq.functional_quantity,
            "damaged_quantity": eq.damaged_quantity,
            "under_maintenance_quantity": eq.under_maintenance_quantity,
            "partially_functional_quantity": eq.partially_functional_quantity,
            "repairable_units": repairable_units,
            "affected_experiments_count": len(linked_experiments),
            "affected_experiments": linked_experiments,
            "affected_students_count": total_students_impacted,
            "potential_capacity_gain": potential_capacity_gain,
            "reason_for_priority": reason,
            "expected_coverage_improvement": expected_improvement,
            "suggested_action": suggested_action,
            "repair_status": eq.repair_status
        })

    # Sort recommendations: Critical first, then High, Medium, Low, then by affected students descending
    priority_order = {"Critical": 0, "High": 1, "Medium": 2, "Low": 3}
    recommendations.sort(
        key=lambda x: (priority_order.get(x["priority"], 99), -x["affected_students_count"], -x["repairable_units"])
    )

    return recommendations
