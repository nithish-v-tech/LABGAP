from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database.connection import get_db
from app.database.models import Equipment, Laboratory, ExperimentEquipment, Experiment, User
from app.schemas.schemas import EquipmentCreate, EquipmentUpdate, EquipmentResponse
from app.security.permissions import require_admin, require_all_authenticated

router = APIRouter(prefix="/equipment", tags=["Equipment"])

def validate_equipment_quantities(total: int, functional: int, partial: int, damaged: int, maintenance: int):
    if total < 0 or functional < 0 or partial < 0 or damaged < 0 or maintenance < 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Equipment quantities cannot be negative."
        )
    if total != (functional + partial + damaged + maintenance):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                f"Validation error: Sum of condition quantities ({functional} functional + {partial} partially functional + "
                f"{damaged} damaged + {maintenance} maintenance = {functional + partial + damaged + maintenance}) "
                f"must strictly equal total quantity ({total})."
            )
        )

@router.get("/", response_model=List[dict])
def list_equipment(
    laboratory_id: Optional[int] = None,
    condition: Optional[str] = None,
    search: Optional[str] = None,
    current_user: User = Depends(require_all_authenticated),
    db: Session = Depends(get_db)
):
    query = db.query(Equipment)
    if laboratory_id:
        query = query.filter(Equipment.laboratory_id == laboratory_id)
    if search:
        query = query.filter(
            (Equipment.name.ilike(f"%{search}%")) |
            (Equipment.equipment_code.ilike(f"%{search}%"))
        )

    items = query.all()
    results = []
    for eq in items:
        # Check condition filter
        if condition:
            cond = condition.lower()
            if cond == "functional" and eq.functional_quantity == 0:
                continue
            elif cond == "damaged" and eq.damaged_quantity == 0:
                continue
            elif cond == "maintenance" and eq.under_maintenance_quantity == 0:
                continue
            elif cond == "partial" and eq.partially_functional_quantity == 0:
                continue

        # Count associated experiments
        exp_count = db.query(ExperimentEquipment).filter(ExperimentEquipment.equipment_id == eq.id).count()

        results.append({
            "id": eq.id,
            "laboratory_id": eq.laboratory_id,
            "laboratory_name": eq.laboratory.name if eq.laboratory else "Unknown",
            "equipment_code": eq.equipment_code,
            "name": eq.name,
            "description": eq.description,
            "total_quantity": eq.total_quantity,
            "functional_quantity": eq.functional_quantity,
            "partially_functional_quantity": eq.partially_functional_quantity,
            "damaged_quantity": eq.damaged_quantity,
            "under_maintenance_quantity": eq.under_maintenance_quantity,
            "available_quantity": eq.functional_quantity,  # Damaged and maintenance are NOT counted
            "maintenance_status": eq.maintenance_status,
            "repair_status": eq.repair_status,
            "associated_experiments_count": exp_count,
            "created_at": eq.created_at,
            "updated_at": eq.updated_at
        })

    return results

@router.get("/{eq_id}")
def get_equipment_detail(
    eq_id: int,
    current_user: User = Depends(require_all_authenticated),
    db: Session = Depends(get_db)
):
    eq = db.query(Equipment).filter(Equipment.id == eq_id).first()
    if not eq:
        raise HTTPException(status_code=404, detail="Equipment not found")

    links = db.query(ExperimentEquipment).filter(ExperimentEquipment.equipment_id == eq.id).all()
    associated_exps = []
    for l in links:
        exp = db.query(Experiment).filter(Experiment.id == l.experiment_id).first()
        if exp:
            associated_exps.append({
                "experiment_id": exp.id,
                "experiment_code": exp.experiment_code,
                "name": exp.name,
                "quantity_required": l.quantity_required,
                "is_critical": l.is_critical
            })

    return {
        "id": eq.id,
        "laboratory_id": eq.laboratory_id,
        "laboratory_name": eq.laboratory.name if eq.laboratory else "Unknown",
        "equipment_code": eq.equipment_code,
        "name": eq.name,
        "description": eq.description,
        "total_quantity": eq.total_quantity,
        "functional_quantity": eq.functional_quantity,
        "partially_functional_quantity": eq.partially_functional_quantity,
        "damaged_quantity": eq.damaged_quantity,
        "under_maintenance_quantity": eq.under_maintenance_quantity,
        "maintenance_status": eq.maintenance_status,
        "repair_status": eq.repair_status,
        "associated_experiments": associated_exps
    }

@router.post("/", response_model=EquipmentResponse)
def create_equipment(
    payload: EquipmentCreate,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    existing = db.query(Equipment).filter(Equipment.equipment_code == payload.equipment_code).first()
    if existing:
        raise HTTPException(status_code=400, detail="Equipment with this code already exists")

    lab = db.query(Laboratory).filter(Laboratory.id == payload.laboratory_id).first()
    if not lab:
        raise HTTPException(status_code=400, detail="Laboratory does not exist")

    validate_equipment_quantities(
        payload.total_quantity,
        payload.functional_quantity,
        payload.partially_functional_quantity,
        payload.damaged_quantity,
        payload.under_maintenance_quantity
    )

    eq = Equipment(
        laboratory_id=payload.laboratory_id,
        equipment_code=payload.equipment_code,
        name=payload.name,
        description=payload.description,
        total_quantity=payload.total_quantity,
        functional_quantity=payload.functional_quantity,
        partially_functional_quantity=payload.partially_functional_quantity,
        damaged_quantity=payload.damaged_quantity,
        under_maintenance_quantity=payload.under_maintenance_quantity,
        maintenance_status=payload.maintenance_status,
        repair_status=payload.repair_status
    )
    db.add(eq)
    db.commit()
    db.refresh(eq)
    return eq

@router.put("/{eq_id}", response_model=EquipmentResponse)
def update_equipment(
    eq_id: int,
    payload: EquipmentUpdate,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    eq = db.query(Equipment).filter(Equipment.id == eq_id).first()
    if not eq:
        raise HTTPException(status_code=404, detail="Equipment not found")

    new_total = payload.total_quantity if payload.total_quantity is not None else eq.total_quantity
    new_func = payload.functional_quantity if payload.functional_quantity is not None else eq.functional_quantity
    new_part = payload.partially_functional_quantity if payload.partially_functional_quantity is not None else eq.partially_functional_quantity
    new_dam = payload.damaged_quantity if payload.damaged_quantity is not None else eq.damaged_quantity
    new_maint = payload.under_maintenance_quantity if payload.under_maintenance_quantity is not None else eq.under_maintenance_quantity

    validate_equipment_quantities(new_total, new_func, new_part, new_dam, new_maint)

    for field, val in payload.dict(exclude_unset=True).items():
        setattr(eq, field, val)

    db.commit()
    db.refresh(eq)
    return eq

@router.delete("/{eq_id}")
def delete_equipment(
    eq_id: int,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    eq = db.query(Equipment).filter(Equipment.id == eq_id).first()
    if not eq:
        raise HTTPException(status_code=404, detail="Equipment not found")

    db.delete(eq)
    db.commit()
    return {"message": "Equipment deleted successfully"}
