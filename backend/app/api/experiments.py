from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from app.database.connection import get_db
from app.database.models import Experiment, ExperimentEquipment, Equipment, Laboratory, StudentBatch, User
from app.schemas.schemas import ExperimentCreate, ExperimentUpdate, ExperimentResponse
from app.security.permissions import require_admin, require_all_authenticated
from app.algorithms.capacity_engine import calculate_experiment_capacity

router = APIRouter(prefix="/experiments", tags=["Experiments"])

@router.get("/")
def list_experiments(
    laboratory_id: Optional[int] = None,
    search: Optional[str] = None,
    coverage: Optional[str] = None,
    current_user: User = Depends(require_all_authenticated),
    db: Session = Depends(get_db)
):
    query = db.query(Experiment)
    if laboratory_id:
        query = query.filter(Experiment.laboratory_id == laboratory_id)
    if search:
        query = query.filter(
            (Experiment.name.ilike(f"%{search}%")) |
            (Experiment.experiment_code.ilike(f"%{search}%")) |
            (Experiment.practical_competency.ilike(f"%{search}%"))
        )

    experiments = query.all()
    default_batch = db.query(StudentBatch).first()

    results = []
    for exp in experiments:
        # Calculate coverage on the fly
        capacity_info = calculate_experiment_capacity(db, exp, default_batch)
        exp_classification = capacity_info["classification"]

        if coverage and coverage.upper() != "ALL" and exp_classification != coverage.upper():
            continue

        reqs = db.query(ExperimentEquipment).filter(ExperimentEquipment.experiment_id == exp.id).all()
        equipment_details = []
        for r in reqs:
            eq = db.query(Equipment).filter(Equipment.id == r.equipment_id).first()
            if eq:
                equipment_details.append({
                    "equipment_id": eq.id,
                    "equipment_code": eq.equipment_code,
                    "equipment_name": eq.name,
                    "quantity_required": r.quantity_required,
                    "functional_available": eq.functional_quantity,
                    "is_critical": r.is_critical
                })

        results.append({
            "id": exp.id,
            "experiment_code": exp.experiment_code,
            "name": exp.name,
            "description": exp.description,
            "laboratory_id": exp.laboratory_id,
            "laboratory_name": exp.laboratory.name if exp.laboratory else "N/A",
            "practical_competency": exp.practical_competency,
            "equipment_quantity_per_session": exp.equipment_quantity_per_session,
            "students_per_unit": exp.students_per_unit,
            "min_safe_batch_size": exp.min_safe_batch_size,
            "max_safe_batch_size": exp.max_safe_batch_size,
            "duration_hours": exp.duration_hours,
            "required_sessions": exp.required_sessions,
            "completion_criteria": exp.completion_criteria,
            "equipment_requirements": equipment_details,
            "coverage_classification": exp_classification,
            "safe_capacity_per_session": capacity_info["safe_capacity_per_session"],
            "equipment_shortage": capacity_info["equipment_shortage"],
            "reason": capacity_info["reason"]
        })

    return results

@router.get("/{exp_id}")
def get_experiment_detail(
    exp_id: int,
    current_user: User = Depends(require_all_authenticated),
    db: Session = Depends(get_db)
):
    exp = db.query(Experiment).filter(Experiment.id == exp_id).first()
    if not exp:
        raise HTTPException(status_code=404, detail="Experiment not found")

    default_batch = db.query(StudentBatch).first()
    capacity_info = calculate_experiment_capacity(db, exp, default_batch)

    reqs = db.query(ExperimentEquipment).filter(ExperimentEquipment.experiment_id == exp.id).all()
    equipment_details = []
    for r in reqs:
        eq = db.query(Equipment).filter(Equipment.id == r.equipment_id).first()
        if eq:
            equipment_details.append({
                "equipment_id": eq.id,
                "equipment_code": eq.equipment_code,
                "equipment_name": eq.name,
                "quantity_required": r.quantity_required,
                "functional_available": eq.functional_quantity,
                "damaged": eq.damaged_quantity,
                "under_maintenance": eq.under_maintenance_quantity,
                "is_critical": r.is_critical
            })

    return {
        "id": exp.id,
        "experiment_code": exp.experiment_code,
        "name": exp.name,
        "description": exp.description,
        "laboratory_id": exp.laboratory_id,
        "laboratory_name": exp.laboratory.name if exp.laboratory else "N/A",
        "practical_competency": exp.practical_competency,
        "equipment_quantity_per_session": exp.equipment_quantity_per_session,
        "students_per_unit": exp.students_per_unit,
        "min_safe_batch_size": exp.min_safe_batch_size,
        "max_safe_batch_size": exp.max_safe_batch_size,
        "duration_hours": exp.duration_hours,
        "required_sessions": exp.required_sessions,
        "completion_criteria": exp.completion_criteria,
        "equipment_requirements": equipment_details,
        "coverage_analysis": capacity_info
    }

@router.post("/")
def create_experiment(
    payload: ExperimentCreate,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    existing = db.query(Experiment).filter(Experiment.experiment_code == payload.experiment_code).first()
    if existing:
        raise HTTPException(status_code=400, detail="Experiment code already exists")

    lab = db.query(Laboratory).filter(Laboratory.id == payload.laboratory_id).first()
    if not lab:
        raise HTTPException(status_code=400, detail="Laboratory does not exist")

    exp = Experiment(
        laboratory_id=payload.laboratory_id,
        experiment_code=payload.experiment_code,
        name=payload.name,
        description=payload.description,
        practical_competency=payload.practical_competency,
        equipment_quantity_per_session=payload.equipment_quantity_per_session,
        students_per_unit=payload.students_per_unit,
        min_safe_batch_size=payload.min_safe_batch_size,
        max_safe_batch_size=payload.max_safe_batch_size,
        duration_hours=payload.duration_hours,
        required_sessions=payload.required_sessions,
        completion_criteria=payload.completion_criteria
    )
    db.add(exp)
    db.flush()

    if payload.equipment_requirements:
        for req in payload.equipment_requirements:
            eq_link = ExperimentEquipment(
                experiment_id=exp.id,
                equipment_id=req.equipment_id,
                quantity_required=req.quantity_required,
                is_critical=req.is_critical
            )
            db.add(eq_link)

    db.commit()
    db.refresh(exp)
    return {"message": "Experiment created successfully", "id": exp.id, "experiment_code": exp.experiment_code}

@router.put("/{exp_id}")
def update_experiment(
    exp_id: int,
    payload: ExperimentUpdate,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    exp = db.query(Experiment).filter(Experiment.id == exp_id).first()
    if not exp:
        raise HTTPException(status_code=404, detail="Experiment not found")

    update_data = payload.dict(exclude_unset=True)
    eq_reqs = update_data.pop("equipment_requirements", None)

    for field, val in update_data.items():
        setattr(exp, field, val)

    if eq_reqs is not None:
        db.query(ExperimentEquipment).filter(ExperimentEquipment.experiment_id == exp.id).delete()
        for req in eq_reqs:
            eq_link = ExperimentEquipment(
                experiment_id=exp.id,
                equipment_id=req["equipment_id"],
                quantity_required=req.get("quantity_required", 1),
                is_critical=req.get("is_critical", True)
            )
            db.add(eq_link)

    db.commit()
    db.refresh(exp)
    return {"message": "Experiment updated successfully", "id": exp.id}

@router.delete("/{exp_id}")
def delete_experiment(
    exp_id: int,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    exp = db.query(Experiment).filter(Experiment.id == exp_id).first()
    if not exp:
        raise HTTPException(status_code=404, detail="Experiment not found")

    db.delete(exp)
    db.commit()
    return {"message": "Experiment deleted successfully"}
