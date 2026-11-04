import pytest
from app.api.equipment import validate_equipment_quantities
from fastapi import HTTPException

def test_equipment_quantities_validation_valid():
    # 10 total = 7 functional + 1 partial + 2 damaged + 0 under maintenance -> Valid!
    validate_equipment_quantities(10, 7, 1, 2, 0)

def test_equipment_quantities_validation_negative():
    with pytest.raises(HTTPException) as exc_info:
        validate_equipment_quantities(10, -2, 0, 12, 0)
    assert exc_info.value.status_code == 400
    assert "cannot be negative" in exc_info.value.detail

def test_equipment_quantities_validation_sum_mismatch():
    # 10 total != 5 functional + 1 partial + 1 damaged + 1 maintenance (total 8) -> Mismatch!
    with pytest.raises(HTTPException) as exc_info:
        validate_equipment_quantities(10, 5, 1, 1, 1)
    assert exc_info.value.status_code == 400
    assert "must strictly equal total quantity" in exc_info.value.detail
