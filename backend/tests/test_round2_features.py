import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from fastapi import HTTPException
from app.database.connection import Base
from app.database.models import (
    Institution, Department, Role, User, Laboratory, Faculty,
    StudentBatch, Student, Equipment, Experiment, ExperimentEquipment,
    BatchExperiment, CompletionRecord, Schedule
)
from app.algorithms.smart_allocation_engine import evaluate_smart_laboratory_allocations
from app.api.schedule import approve_laboratory_allocation, get_smart_lab_recommendations
from app.api.analysis import get_student_competency_matrix, get_resource_intelligence
from app.schemas.schemas import ApproveAllocationRequest

@pytest.fixture
def r2_db():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(bind=engine)
    session = Session()

    inst = Institution(name="Apex Tech", code="APEX")
    session.add(inst)
    session.flush()

    dept = Department(name="Electrical & Electronics", code="EEE", institution_id=inst.id)
    session.add(dept)
    session.flush()

    admin_role = Role(name="admin", description="Admin")
    fac_role = Role(name="faculty", description="Faculty")
    stu_role = Role(name="student", description="Student")
    session.add_all([admin_role, fac_role, stu_role])
    session.flush()

    admin_u = User(email="admin@test.com", hashed_password="pw", full_name="Admin", role_id=admin_role.id, department_id=dept.id)
    fac_u = User(email="fac@test.com", hashed_password="pw", full_name="Dr. Rao", role_id=fac_role.id, department_id=dept.id)
    stu_u = User(email="stu@test.com", hashed_password="pw", full_name="Student", role_id=stu_role.id, department_id=dept.id)
    session.add_all([admin_u, fac_u, stu_u])
    session.flush()

    fac_profile = Faculty(user_id=fac_u.id, department_id=dept.id, faculty_code="F-RAO", name="Dr. Rao", email="fac@test.com")
    session.add(fac_profile)
    session.flush()

    # Create 2 laboratories: Lab A (Fully equipped), Lab B (Broken equipment)
    lab_a = Laboratory(name="Circuits Lab A", code="LAB-A", location="Room 101", max_student_capacity=30, department_id=dept.id, open_time="09:00", close_time="17:00")
    lab_b = Laboratory(name="Circuits Lab B", code="LAB-B", location="Room 102", max_student_capacity=30, department_id=dept.id, open_time="09:00", close_time="17:00")
    session.add_all([lab_a, lab_b])
    session.flush()

    # Lab A equipment: 8 functional oscilloscopes
    eq_a = Equipment(laboratory_id=lab_a.id, equipment_code="EQ-OSC-A", name="Oscilloscope", total_quantity=8, functional_quantity=8, damaged_quantity=0, under_maintenance_quantity=0)
    # Lab B equipment: 0 functional oscilloscopes (all damaged)
    eq_b = Equipment(laboratory_id=lab_b.id, equipment_code="EQ-OSC-B", name="Oscilloscope", total_quantity=8, functional_quantity=0, damaged_quantity=8, under_maintenance_quantity=0)
    session.add_all([eq_a, eq_b])
    session.flush()

    # Batch with 16 students
    batch = StudentBatch(batch_code="B-2026-ALPHA", batch_name="Alpha Batch", department_id=dept.id, number_of_students=16)
    session.add(batch)
    session.flush()

    s1 = Student(student_id_number="STU-001", name="John Doe", email="john@test.com", department_id=dept.id, batch_id=batch.id)
    s2 = Student(student_id_number="STU-002", name="Jane Smith", email="jane@test.com", department_id=dept.id, batch_id=batch.id)
    session.add_all([s1, s2])
    session.flush()

    # Experiment requiring 1 oscilloscope per station, 2 students per station
    exp = Experiment(
        laboratory_id=lab_a.id, experiment_code="EXP-ANALOG", name="Op-Amp Filtering",
        practical_competency="Analog Signal Processing", students_per_unit=2, duration_hours=2.0
    )
    session.add(exp)
    session.flush()
    session.add(ExperimentEquipment(experiment_id=exp.id, equipment_id=eq_a.id, quantity_required=1, is_critical=True))
    session.add(BatchExperiment(batch_id=batch.id, experiment_id=exp.id))
    session.commit()

    yield {
        "db": session, "admin": admin_u, "faculty": fac_u, "student": stu_u,
        "batch": batch, "exp": exp, "lab_a": lab_a, "lab_b": lab_b, "s1": s1, "s2": s2
    }
    session.close()

def test_smart_lab_allocation_ranking_and_rejection(r2_db):
    db = r2_db["db"]
    batch = r2_db["batch"]
    exp = r2_db["exp"]
    lab_a = r2_db["lab_a"]
    lab_b = r2_db["lab_b"]

    res = evaluate_smart_laboratory_allocations(db, experiment_id=exp.id, batch_id=batch.id)
    assert res["has_feasible_lab"] is True
    assert res["best_recommendation"]["laboratory_id"] == lab_a.id
    assert res["best_recommendation"]["suitability_score"] > 80.0
    assert res["best_recommendation"]["is_feasible"] is True

    # Lab B must be rejected due to zero functional oscilloscopes
    assert len(res["rejected_laboratories"]) >= 1
    rejected_b = next(r for r in res["rejected_laboratories"] if r["laboratory_id"] == lab_b.id)
    assert rejected_b["is_feasible"] is False
    assert any("functional" in r.lower() or "damaged" in r.lower() for r in rejected_b["rejection_reasons"])

def test_approve_allocation_success_and_infeasible_rejection(r2_db):
    db = r2_db["db"]
    admin = r2_db["admin"]
    batch = r2_db["batch"]
    exp = r2_db["exp"]
    lab_a = r2_db["lab_a"]
    lab_b = r2_db["lab_b"]

    # 1. Rejecting infeasible allocation to Lab B
    bad_req = ApproveAllocationRequest(experiment_id=exp.id, batch_id=batch.id, laboratory_id=lab_b.id)
    with pytest.raises(HTTPException) as excinfo:
        approve_laboratory_allocation(payload=bad_req, current_user=admin, db=db)
    assert excinfo.value.status_code == 400
    assert "infeasible" in excinfo.value.detail.lower()

    # 2. Approving feasible allocation to Lab A
    good_req = ApproveAllocationRequest(experiment_id=exp.id, batch_id=batch.id, laboratory_id=lab_a.id, start_date="2026-11-15")
    appr_res = approve_laboratory_allocation(payload=good_req, current_user=admin, db=db)
    assert appr_res["success"] is True
    assert appr_res["sessions_scheduled"] >= 1

    # Verify sessions are in the database
    schedules = db.query(Schedule).filter(Schedule.batch_id == batch.id, Schedule.laboratory_id == lab_a.id).all()
    assert len(schedules) >= 1

def test_student_competency_matrix_and_resource_intelligence(r2_db):
    db = r2_db["db"]
    admin = r2_db["admin"]
    batch = r2_db["batch"]
    exp = r2_db["exp"]
    s1 = r2_db["s1"]
    s2 = r2_db["s2"]

    # Student 1 is completed and verified
    rec1 = CompletionRecord(
        student_id=s1.id, experiment_id=exp.id, batch_id=batch.id,
        participation_status="Completed", verification_status="Verified"
    )
    # Student 2 only participated, NOT verified
    rec2 = CompletionRecord(
        student_id=s2.id, experiment_id=exp.id, batch_id=batch.id,
        participation_status="Completed", verification_status="Pending"
    )
    db.add_all([rec1, rec2])
    db.commit()

    # 1. Competency Matrix Test
    comp_res = get_student_competency_matrix(batch_id=batch.id, current_user=admin, db=db)
    assert comp_res["cohort_summary"]["total_students"] == 2
    assert comp_res["cohort_summary"]["total_verified_tasks"] == 1
    assert comp_res["cohort_summary"]["students_with_gaps_count"] == 1

    s1_data = next(s for s in comp_res["students"] if s["student_id"] == s1.id)
    s2_data = next(s for s in comp_res["students"] if s["student_id"] == s2.id)
    assert s1_data["verified_practicals"] == 1
    assert s1_data["status_level"] == "Proficient"
    assert s2_data["verified_practicals"] == 0
    assert s2_data["status_level"] == "At Risk"

    # 2. Resource Intelligence Test
    intel = get_resource_intelligence(current_user=admin, db=db)
    assert intel["total_recommendations"] > 0
    # Must flag broken oscilloscopes in Lab B
    repair_recs = [r for r in intel["recommendations"] if r["category"] == "Equipment Repair Impact"]
    assert len(repair_recs) >= 1
    assert any("Oscilloscope" in r["title"] for r in repair_recs)
