import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from fastapi import HTTPException
from app.database.connection import Base
from app.database.models import (
    Institution, Department, Role, User, Laboratory, Faculty,
    StudentBatch, Student, Equipment, Experiment, ExperimentEquipment,
    BatchExperiment, CompletionRecord, Schedule, RepairRecord
)
from app.security.auth import hash_password, create_access_token
from app.schemas.schemas import (
    LoginRequest, LaboratoryCreate, LaboratoryUpdate, StudentBatchCreate,
    CompletionRecordCreate, CompletionRecordVerify, RepairConfirmRequest,
    ScheduleCreateRequest, AutoAllocateRequest
)
from app.api.auth import login, get_current_user_profile
from app.api.laboratories import list_laboratories, create_laboratory, update_laboratory
from app.api.equipment import list_equipment, create_equipment
from app.api.experiments import list_experiments, create_experiment
from app.api.batches import list_batches, create_batch, assign_experiments_to_batch, get_batch_detail
from app.api.verification import record_student_participation, verify_completion_record, list_completion_records
from app.api.repairs import get_repair_recommendations, confirm_equipment_repair
from app.api.schedule import list_schedules, generate_schedule_plan, auto_allocate_curriculum, clear_all_schedules
from app.api.analysis import run_full_analysis, get_dashboard_summary
from app.api.students import get_student_portal_data
from app.algorithms.gap_analyzer import calculate_student_learning_gap

@pytest.fixture
def integrated_db():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(bind=engine)
    session = Session()

    # Seed core entities
    inst = Institution(name="Apex Engineering University", code="AEU")
    session.add(inst)
    session.flush()

    dept = Department(name="Electrical & Electronics", code="EEE", institution_id=inst.id)
    session.add(dept)
    session.flush()

    admin_role = Role(name="admin", description="Admin")
    fac_role = Role(name="faculty", description="Faculty")
    stu_role = Role(name="student", description="Student")
    hod_role = Role(name="hod", description="HOD")
    session.add_all([admin_role, fac_role, stu_role, hod_role])
    session.flush()

    admin_u = User(email="admin@test.com", hashed_password=hash_password("pw123"), full_name="Admin", role_id=admin_role.id, department_id=dept.id)
    fac_u = User(email="fac@test.com", hashed_password=hash_password("pw123"), full_name="Faculty", role_id=fac_role.id, department_id=dept.id)
    stu_u = User(email="stu@test.com", hashed_password=hash_password("pw123"), full_name="Student", role_id=stu_role.id, department_id=dept.id)
    hod_u = User(email="hod@test.com", hashed_password=hash_password("pw123"), full_name="HOD", role_id=hod_role.id, department_id=dept.id)
    session.add_all([admin_u, fac_u, stu_u, hod_u])
    session.flush()

    fac_profile = Faculty(user_id=fac_u.id, department_id=dept.id, faculty_code="F-01", name="Prof. Smith", email="fac@test.com")
    session.add(fac_profile)
    session.flush()

    yield {
        "db": session, "dept": dept, "admin": admin_u,
        "faculty": fac_u, "student": stu_u, "hod": hod_u, "fac_profile": fac_profile
    }
    session.close()

def test_auth_endpoints_login_and_me(integrated_db):
    db = integrated_db["db"]
    admin = integrated_db["admin"]

    # 1. Successful login
    req = LoginRequest(email="admin@test.com", password="pw123")
    res = login(request=req, db=db)
    assert "access_token" in res
    assert res["user"]["email"] == "admin@test.com"
    assert res["user"]["role"] == "admin"

    # 2. Failed login with bad password
    bad_req = LoginRequest(email="admin@test.com", password="wrongpassword")
    with pytest.raises(HTTPException) as excinfo:
        login(request=bad_req, db=db)
    assert excinfo.value.status_code == 401

    # 3. get_current_user_profile endpoint
    me = get_current_user_profile(current_user=admin, db=db)
    assert me["email"] == "admin@test.com"
    assert me["role"] == "admin"

def test_laboratories_crud_endpoints(integrated_db):
    db = integrated_db["db"]
    admin = integrated_db["admin"]
    dept = integrated_db["dept"]

    # Create laboratory
    lab_req = LaboratoryCreate(
        code="LAB-VLSI", name="VLSI & Embedded Lab", location="Room 304",
        max_student_capacity=25, department_id=dept.id, open_time="09:00", close_time="17:00"
    )
    created = create_laboratory(payload=lab_req, current_user=admin, db=db)
    assert created.id is not None
    assert created.code == "LAB-VLSI"

    # List laboratories
    all_labs = list_laboratories(current_user=admin, db=db)
    assert len(all_labs) == 1
    assert all_labs[0]["code"] == "LAB-VLSI"

    # Update laboratory
    upd_req = LaboratoryUpdate(name="Advanced VLSI Systems Lab", max_student_capacity=28)
    updated = update_laboratory(lab_id=created.id, payload=upd_req, current_user=admin, db=db)
    assert updated.name == "Advanced VLSI Systems Lab"
    assert updated.max_student_capacity == 28

def test_equipment_and_experiment_mapping_endpoints(integrated_db):
    db = integrated_db["db"]
    admin = integrated_db["admin"]
    dept = integrated_db["dept"]

    # Create Lab
    lab = Laboratory(name="Power Lab", code="L-POW", location="Room 101", department_id=dept.id, open_time="09:00", close_time="17:00")
    db.add(lab)
    db.flush()

    # Create Equipment
    from app.schemas.schemas import EquipmentCreate
    eq_req = EquipmentCreate(
        laboratory_id=lab.id, equipment_code="EQ-TRANS", name="Single Phase Transformer",
        total_quantity=6, functional_quantity=4, damaged_quantity=2,
        partially_functional_quantity=0, under_maintenance_quantity=0
    )
    eq = create_equipment(payload=eq_req, current_user=admin, db=db)
    assert eq.id is not None
    assert eq.functional_quantity == 4
    assert eq.damaged_quantity == 2

    # Create Experiment with mapped equipment
    from app.schemas.schemas import ExperimentCreate, ExperimentEquipmentReq
    exp_req = ExperimentCreate(
        laboratory_id=lab.id, experiment_code="EXP-TRANS-OC", name="Transformer Open Circuit Test",
        practical_competency="Transformer Diagnostics", students_per_unit=2, duration_hours=2.0,
        completion_criteria="Calibrated readings and viva",
        equipment_requirements=[ExperimentEquipmentReq(equipment_id=eq.id, quantity_required=1, is_critical=True)]
    )
    exp = create_experiment(payload=exp_req, current_user=admin, db=db)
    assert exp["id"] is not None
    assert exp["experiment_code"] == "EXP-TRANS-OC"

def test_batch_and_verification_workflow(integrated_db):
    db = integrated_db["db"]
    admin = integrated_db["admin"]
    faculty = integrated_db["faculty"]
    dept = integrated_db["dept"]

    lab = Laboratory(name="Analog Lab", code="L-ANA", location="Room 102", department_id=dept.id, open_time="09:00", close_time="17:00")
    db.add(lab)
    db.flush()

    # Create Batch
    batch_req = StudentBatchCreate(
        batch_code="B-2026-A", batch_name="Cohort 2026-A", department_id=dept.id,
        laboratory_id=lab.id, number_of_students=2
    )
    batch = create_batch(payload=batch_req, current_user=admin, db=db)

    # Add Students
    s1 = Student(student_id_number="S-101", name="Alice", email="alice@test.com", department_id=dept.id, batch_id=batch.id)
    s2 = Student(student_id_number="S-102", name="Bob", email="bob@test.com", department_id=dept.id, batch_id=batch.id)
    db.add_all([s1, s2])
    db.flush()

    # Create Experiment & Assign
    exp = Experiment(laboratory_id=lab.id, experiment_code="EXP-DIODE", name="Diode Test", practical_competency="Diodes", duration_hours=2.0)
    db.add(exp)
    db.flush()
    assign_experiments_to_batch(batch_id=batch.id, experiment_ids=[exp.id], current_user=admin, db=db)

    # 1. Record completion by student
    comp_req = CompletionRecordCreate(student_id=s1.id, experiment_id=exp.id, batch_id=batch.id, participation_status="Completed")
    rec = record_student_participation(payload=comp_req, current_user=faculty, db=db)
    assert rec["id"] is not None

    # 2. Verify completion by faculty instructor
    verify_req = CompletionRecordVerify(verification_status="Verified", assessment_notes="Excellent circuit wiring")
    v_rec = verify_completion_record(record_id=rec["id"], payload=verify_req, current_user=faculty, db=db)
    assert v_rec["verification_status"] == "Verified"

    # 3. Learning gap analysis verifies Alice is completed, Bob has gap
    portal_alice = get_student_portal_data(student_id=s1.id, current_user=admin, db=db)
    portal_bob = get_student_portal_data(student_id=s2.id, current_user=admin, db=db)
    assert portal_alice["verified_completed_count"] == 1
    assert portal_alice["pending_experiments_count"] == 0
    assert portal_bob["verified_completed_count"] == 0
    assert portal_bob["pending_experiments_count"] == 1

    # And check calculate_student_learning_gap
    batch_gap = calculate_student_learning_gap(db=db, experiment_id=exp.id, batch_id=batch.id)
    assert batch_gap["total_assigned"] == 2
    assert batch_gap["verified_completed"] == 1
    assert batch_gap["unverified_learning_gap"] == 1

def test_repair_workflow_and_schedule_auto_allocation(integrated_db):
    db = integrated_db["db"]
    admin = integrated_db["admin"]
    dept = integrated_db["dept"]

    lab = Laboratory(name="Control Systems Lab", code="L-CTRL", location="Room 205", department_id=dept.id, open_time="09:00", close_time="17:00")
    db.add(lab)
    db.flush()

    eq = Equipment(
        laboratory_id=lab.id, equipment_code="EQ-PID", name="PID Controller Kit",
        total_quantity=4, functional_quantity=1, damaged_quantity=3,
        partially_functional_quantity=0, under_maintenance_quantity=0
    )
    db.add(eq)
    db.flush()

    batch = StudentBatch(batch_code="B-CTRL", batch_name="Control Batch", department_id=dept.id, laboratory_id=lab.id, number_of_students=8)
    db.add(batch)
    db.flush()

    exp = Experiment(
        laboratory_id=lab.id, experiment_code="EXP-PID", name="PID Tuning",
        practical_competency="Feedback Loops", students_per_unit=2, duration_hours=2.0
    )
    db.add(exp)
    db.flush()
    db.add(ExperimentEquipment(experiment_id=exp.id, equipment_id=eq.id, quantity_required=1))
    db.add(BatchExperiment(batch_id=batch.id, experiment_id=exp.id))
    db.commit()

    # 1. Repair recommendations endpoint
    recs = get_repair_recommendations(current_user=admin, db=db)
    assert len(recs) >= 1
    assert any(r["equipment_code"] == "EQ-PID" for r in recs)

    # 2. Confirm repair endpoint restores 3 units
    conf_req = RepairConfirmRequest(equipment_id=eq.id, units_to_restore=3)
    c_res = confirm_equipment_repair(payload=conf_req, current_user=admin, db=db)
    assert c_res["new_functional_quantity"] == 4
    assert c_res["new_damaged_quantity"] == 0

    # 3. Auto-allocate curriculum
    alloc_req = AutoAllocateRequest(batch_ids=[batch.id], start_date="2026-11-12", clear_existing=True)
    alloc_res = auto_allocate_curriculum(payload=alloc_req, current_user=admin, db=db)
    assert alloc_res["success"] is True
    assert alloc_res["total_sessions_allocated"] >= 1

    # 4. List schedules endpoint verifies persistence
    sched_list = list_schedules(current_user=admin, db=db)
    assert len(sched_list) >= 1
    assert any(s["batch_code"] == "B-CTRL" for s in sched_list)
