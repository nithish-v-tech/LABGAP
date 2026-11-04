import datetime
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database.connection import get_db
from app.database.models import Equipment, RepairRecord, User
from app.schemas.schemas import RepairConfirmRequest
from app.security.permissions import require_admin, require_admin_or_hod, require_all_authenticated
from app.algorithms.repair_engine import evaluate_equipment_repairs

router = APIRouter(prefix="/repairs", tags=["Repair Recommendations"])

@router.get("/recommendations")
def get_repair_recommendations(
    current_user: User = Depends(require_all_authenticated),
    db: Session = Depends(get_db)
):
    """
    Evaluates equipment condition and computes explainable repair priorities
    based on student learning impact and capacity bottlenecks.
    """
    recommendations = evaluate_equipment_repairs(db)
    return recommendations

@router.post("/confirm-repair")
def confirm_equipment_repair(
    payload: RepairConfirmRequest,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """
    Administrator verifies that equipment was physically repaired and calibrated,
    restoring units into active functional status.
    Strictly requires administrator authorization.
    """
    eq = db.query(Equipment).filter(Equipment.id == payload.equipment_id).first()
    if not eq:
        raise HTTPException(status_code=404, detail="Equipment not found")

    units = payload.units_to_restore
    if units <= 0:
        raise HTTPException(status_code=400, detail="Units to restore must be greater than 0")

    repairable = eq.damaged_quantity + eq.under_maintenance_quantity
    if units > repairable:
        raise HTTPException(
            status_code=400,
            detail=f"Cannot restore {units} units. Only {repairable} units are currently damaged or under maintenance."
        )

    # Shift units from damaged first, then under maintenance
    remaining_to_shift = units
    if eq.damaged_quantity > 0:
        take_from_damaged = min(eq.damaged_quantity, remaining_to_shift)
        eq.damaged_quantity -= take_from_damaged
        remaining_to_shift -= take_from_damaged

    if remaining_to_shift > 0 and eq.under_maintenance_quantity > 0:
        take_from_maint = min(eq.under_maintenance_quantity, remaining_to_shift)
        eq.under_maintenance_quantity -= take_from_maint
        remaining_to_shift -= take_from_maint

    eq.functional_quantity += units
    eq.repair_status = "Repaired / Operational" if (eq.damaged_quantity == 0 and eq.under_maintenance_quantity == 0) else "Partially Repaired"

    # Create repair audit record
    repair_log = RepairRecord(
        equipment_id=eq.id,
        priority="Completed",
        current_condition=f"Restored {units} units to functional status",
        affected_experiments_count=0,
        affected_students_count=0,
        equipment_shortage=0,
        potential_capacity_gain=units * 2,
        status="Repaired",
        reason_for_priority="Administrator verified physical repair and recalibration",
        expected_coverage_improvement=f"+{units * 2} safe student capacity restored",
        suggested_action="Returned to laboratory active service",
        confirmed_by=current_user.email
    )
    db.add(repair_log)
    db.commit()
    db.refresh(eq)

    return {
        "message": f"Successfully restored {units} unit(s) of '{eq.name}' to functional inventory.",
        "equipment_id": eq.id,
        "equipment_name": eq.name,
        "new_functional_quantity": eq.functional_quantity,
        "new_damaged_quantity": eq.damaged_quantity,
        "new_under_maintenance_quantity": eq.under_maintenance_quantity,
        "total_quantity": eq.total_quantity,
        "confirmed_by": current_user.email,
        "timestamp": datetime.datetime.utcnow().isoformat()
    }
