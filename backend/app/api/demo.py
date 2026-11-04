from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database.connection import get_db
from app.database.models import User
from app.security.permissions import require_admin, require_all_authenticated
from seed import seed_database

router = APIRouter(prefix="/demo", tags=["Demo Management"])

@router.post("/reset")
def reset_demonstration_data(
    current_user: User = Depends(require_all_authenticated)
):
    """
    Resets the database to the benchmark synthetic dataset:
    - 1 Institution, 1 Department, 4 Laboratories
    - 4 Role Demo Accounts (admin, faculty, student, hod)
    - 20 Equipment types with accurate condition distribution
    - 15 Experiments (Fully Covered, Partially Covered, Not Covered)
    - 68 Synthetic Students in 3 Batches
    - Verified vs pending practical completions
    """
    try:
        seed_database()
        return {
            "success": True,
            "message": "Synthetic demonstration dataset reset successfully.",
            "details": {
                "laboratories": 4,
                "experiments": 15,
                "equipment_types": 20,
                "synthetic_students": 68,
                "batches": 3,
                "coverage_classes": ["FULLY COVERED", "PARTIALLY COVERED", "NOT COVERED"]
            }
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to reset demonstration dataset: {str(e)}"
        )
