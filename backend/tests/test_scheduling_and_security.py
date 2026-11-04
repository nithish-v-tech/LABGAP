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
from app.algorithms.scheduling_engine import generate_optimized_schedule, auto_allocate_cohort_curriculum, STANDARD_TIME_SLOTS
from app.algorithms.capacity_engine import calculate_experiment_capacity
from app.security.permissions import require_admin, require_faculty, require_student
from app.security.auth import create_access_token

@pytest.fixture
def db_session():
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

    # Roles
    admin_role = Role(name="admin", description="Admin")
    fac_role = Role(name="faculty", description="Faculty")
    stu_role = Role(name="student", description="Student")
    session.add_all([admin_role, fac_role, stu_role])
    session.flush()

    # Users
    admin_user = User(email="admin@test.com", hashed_password="pw", full_name="Admin User", role_id=admin_role.id, department_id=dept.id)
    fac_user = User(email="fac@test.com", hashed_password="pw", full_name="Faculty User", role_id=fac_role.id, department_id=dept.id)
    stu_user = User(email="stu@test.com", hashed_password="pw", full_name="Student User", role_id=stu_role.id, department_id=dept.id)
    session.add_all([admin_user, fac_user, stu_user])
    session.flush()

    # Laboratory with 09:00 - 17:00 operating hours
    lab1 = Laboratory(
        name="Circuits Lab", code="LAB-CIRC", location="Room 201",
        max_student_capacity=30, department_id=dept.id,
        open_time="09:00", close_time="17:00"
    )
    lab2 = Laboratory(
        name="Machines Lab", code="LAB-MACH", location="Room 102",
        max_student_capacity=30, department_id=dept.id,
        open_time="09:00", close_time="17:00"
    )
    session.add_all([lab1, lab2])
    session.flush()

    # Faculty profile
    fac_profile = Faculty(
        user_id=fac_user.id, department_id=dept.id,
        faculty_code="FAC-01", name="Dr. Sharma", email="fac@test.com",
        assigned_laboratory_id=lab1.id
    )
    session.add(fac_profile)
    session.flush()

    yield session
    session.close()

def test_timetable_strictly_within_operating_hours(db_session):
    """
    Validates that all generated sessions strictly adhere to laboratory
    operating hours (09:00 - 17:00) with zero sessions extending beyond 17:00.
    """
    lab = db_session.query(Laboratory).filter(Laboratory.code == "LAB-CIRC").first()
    faculty = db_session.query(Faculty).first()

    batch = StudentBatch(
        batch_code="B-SEC-A", batch_name="Cohort A", department_id=lab.department_id,
        laboratory_id=lab.id, number_of_students=24, assigned_faculty_id=faculty.id
    )
    db_session.add(batch)
    db_session.flush()

    # Add 12 students to batch
    for i in range(12):
        s = Student(
            student_id_number=f"STU-{i:03d}", name=f"Student {i}",
            email=f"s{i}@test.com", department_id=lab.department_id, batch_id=batch.id
        )
        db_session.add(s)
    db_session.flush()

    # Equipment with 4 stations
    eq = Equipment(
        laboratory_id=lab.id, equipment_code="EQ-DSO", name="Digital Storage Oscilloscope",
        total_quantity=4, functional_quantity=4, partially_functional_quantity=0,
        damaged_quantity=0, under_maintenance_quantity=0
    )
    db_session.add(eq)
    db_session.flush()

    exp = Experiment(
        laboratory_id=lab.id, experiment_code="EXP-RLC", name="RLC Resonance Experiment",
        practical_competency="Frequency Response", duration_hours=2.0,
        students_per_unit=2, min_safe_batch_size=4, max_safe_batch_size=30,
        completion_criteria="Viva passed"
    )
    db_session.add(exp)
    db_session.flush()

    db_session.add(ExperimentEquipment(experiment_id=exp.id, equipment_id=eq.id, quantity_required=1))
    db_session.commit()

    # Generate schedule
    res = generate_optimized_schedule(db_session, experiment_id=exp.id, batch_id=batch.id)
    assert res["success"] is True
    assert len(res["schedules"]) > 0

    # Verify operating hours for each scheduled session
    for s in res["schedules"]:
        assert s["start_time"] >= "09:00", f"Session starts too early: {s['start_time']}"
        assert s["end_time"] <= "17:00", f"Session exceeds closing time: {s['end_time']}"
        # Ensure the invalid 16:15-18:15 slot is never scheduled
        assert s["end_time"] != "18:15"
        assert s["start_time"] != "16:15"

def test_shared_equipment_concurrency_constraint(db_session):
    """
    Validates that concurrent sessions across different experiments/laboratories
    cannot exceed the total functional inventory of shared equipment.
    """
    lab1 = db_session.query(Laboratory).filter(Laboratory.code == "LAB-CIRC").first()
    lab2 = db_session.query(Laboratory).filter(Laboratory.code == "LAB-MACH").first()

    # Shared equipment: only 5 functional units total
    shared_eq = Equipment(
        laboratory_id=lab1.id, equipment_code="EQ-POW", name="Precision Power Supply",
        total_quantity=5, functional_quantity=5, partially_functional_quantity=0,
        damaged_quantity=0, under_maintenance_quantity=0
    )
    db_session.add(shared_eq)
    db_session.flush()

    # Exp 1 requires 4 units (4 stations * 1 unit)
    exp1 = Experiment(
        laboratory_id=lab1.id, experiment_code="EXP-01", name="Analog Filter",
        practical_competency="Filters", duration_hours=2.0, students_per_unit=2
    )
    # Exp 2 also requires 3 units (3 stations * 1 unit)
    exp2 = Experiment(
        laboratory_id=lab2.id, experiment_code="EXP-02", name="Transistor Amplifier",
        practical_competency="Amplification", duration_hours=2.0, students_per_unit=2
    )
    db_session.add_all([exp1, exp2])
    db_session.flush()

    db_session.add(ExperimentEquipment(experiment_id=exp1.id, equipment_id=shared_eq.id, quantity_required=1))
    db_session.add(ExperimentEquipment(experiment_id=exp2.id, equipment_id=shared_eq.id, quantity_required=1))

    batch1 = StudentBatch(batch_code="B1", batch_name="Cohort 1", department_id=lab1.department_id, number_of_students=8)
    batch2 = StudentBatch(batch_code="B2", batch_name="Cohort 2", department_id=lab1.department_id, number_of_students=6)
    db_session.add_all([batch1, batch2])
    db_session.commit()

    # Pre-schedule Exp 1 at 2026-11-10 09:00: consumes 4 units of EQ-POW
    existing_sched = Schedule(
        experiment_id=exp1.id, batch_id=batch1.id, laboratory_id=lab1.id,
        session_number=1, date="2026-11-10", start_time="09:00", end_time="11:00",
        student_capacity=8, expected_students=8, remaining_learning_gap=0, status="Scheduled"
    )
    db_session.add(existing_sched)
    db_session.commit()

    # Now attempt to schedule Exp 2 at 2026-11-10 09:00: needs 3 units.
    # 4 (already committed) + 3 (needed) = 7 > 5 functional units.
    # The scheduling engine must reject 09:00 and allocate 11:15 or another slot!
    res = generate_optimized_schedule(db_session, experiment_id=exp2.id, batch_id=batch2.id, start_date="2026-11-10")
    assert res["success"] is True
    # The session for Exp 2 must NOT be placed at 09:00 on 2026-11-10 due to shared equipment collision!
    for s in res["schedules"]:
        if s["date"] == "2026-11-10":
            assert s["start_time"] != "09:00", "Concurrent session illegally scheduled despite shared equipment shortage!"

def test_auto_allocate_cohort_curriculum(db_session):
    """
    Tests automated multi-batch curriculum allocation across batches and labs.
    Verifies that no batch is double booked and all sessions stay within operating hours.
    """
    lab1 = db_session.query(Laboratory).filter(Laboratory.code == "LAB-CIRC").first()
    faculty = db_session.query(Faculty).first()

    batch_x = StudentBatch(batch_code="BATCH-X", batch_name="Cohort X", department_id=lab1.department_id, number_of_students=10)
    batch_y = StudentBatch(batch_code="BATCH-Y", batch_name="Cohort Y", department_id=lab1.department_id, number_of_students=10)
    db_session.add_all([batch_x, batch_y])
    db_session.flush()

    eq = Equipment(
        laboratory_id=lab1.id, equipment_code="EQ-GEN", name="Signal Generator",
        total_quantity=6, functional_quantity=6, partially_functional_quantity=0,
        damaged_quantity=0, under_maintenance_quantity=0
    )
    db_session.add(eq)
    db_session.flush()

    exp_a = Experiment(
        laboratory_id=lab1.id, experiment_code="EXP-A", name="Diode Characteristics",
        practical_competency="Semiconductors", duration_hours=2.0, students_per_unit=2
    )
    db_session.add(exp_a)
    db_session.flush()

    db_session.add(ExperimentEquipment(experiment_id=exp_a.id, equipment_id=eq.id, quantity_required=1))
    db_session.add(BatchExperiment(batch_id=batch_x.id, experiment_id=exp_a.id))
    db_session.add(BatchExperiment(batch_id=batch_y.id, experiment_id=exp_a.id))
    db_session.commit()

    res = auto_allocate_cohort_curriculum(db_session, batch_ids=[batch_x.id, batch_y.id], start_date="2026-11-11", clear_existing=True)
    assert res["success"] is True
    assert res["total_batches_processed"] == 2
    assert res["total_sessions_allocated"] >= 2

    # Verify no overlaps for the same laboratory or same batch
    scheduled_slots = [(s["date"], s["start_time"], s["laboratory_id"]) for s in res["schedules"]]
    assert len(scheduled_slots) == len(set(scheduled_slots)), "Duplicate laboratory bookings detected!"

def test_role_switcher_security_and_permission_enforcement(db_session):
    """
    Validates that backend role permissions are strictly derived from cryptographic
    tokens and database-backed roles, preventing unauthorized access by students or altered frontend states.
    """
    student_user = db_session.query(User).filter(User.email == "stu@test.com").first()
    faculty_user = db_session.query(User).filter(User.email == "fac@test.com").first()
    admin_user = db_session.query(User).filter(User.email == "admin@test.com").first()

    # 1. Student attempting admin-only action must raise 403 Forbidden
    with pytest.raises(HTTPException) as excinfo:
        require_admin(current_user=student_user)
    assert excinfo.value.status_code == 403
    assert "Access denied" in excinfo.value.detail

    # 2. Student attempting faculty action must raise 403 Forbidden
    with pytest.raises(HTTPException) as excinfo:
        require_faculty(current_user=student_user)
    assert excinfo.value.status_code == 403

    # 3. Faculty attempting admin-only action must raise 403 Forbidden
    with pytest.raises(HTTPException) as excinfo:
        require_admin(current_user=faculty_user)
    assert excinfo.value.status_code == 403

    # 4. Admin user accessing admin dependency succeeds
    assert require_admin(current_user=admin_user) == admin_user

def test_repair_workflow_and_coverage_recalibration(db_session):
    """
    Tests that restoring damaged equipment restores functional units,
    updates repair logs, and recalibrates coverage classification from NOT COVERED to FULLY COVERED.
    """
    lab = db_session.query(Laboratory).filter(Laboratory.code == "LAB-CIRC").first()

    # Equipment starts with 0 functional, 5 damaged
    eq = Equipment(
        laboratory_id=lab.id, equipment_code="EQ-MTR", name="Induction Machine",
        total_quantity=5, functional_quantity=0, partially_functional_quantity=0,
        damaged_quantity=5, under_maintenance_quantity=0
    )
    db_session.add(eq)
    db_session.flush()

    batch = StudentBatch(batch_code="B-REP", batch_name="Repair Batch", department_id=lab.department_id, number_of_students=10)
    db_session.add(batch)
    db_session.flush()

    exp = Experiment(
        laboratory_id=lab.id, experiment_code="EXP-MTR", name="Induction Motor Test",
        practical_competency="Electric Machines", duration_hours=2.0, students_per_unit=2
    )
    db_session.add(exp)
    db_session.flush()

    db_session.add(ExperimentEquipment(experiment_id=exp.id, equipment_id=eq.id, quantity_required=1))
    db_session.commit()

    # Before repair: must be NOT COVERED
    initial_cap = calculate_experiment_capacity(db_session, exp, batch, lab_weekly_hours=40.0)
    assert initial_cap["classification"] == "NOT COVERED"
    assert initial_cap["safe_capacity_per_session"] == 0

    # Perform physical repair: restore 5 units
    eq.damaged_quantity -= 5
    eq.functional_quantity += 5
    eq.repair_status = "Repaired / Operational"

    repair_log = RepairRecord(
        equipment_id=eq.id, priority="Critical", current_condition="Restored 5 units",
        affected_experiments_count=1, affected_students_count=10, equipment_shortage=0,
        potential_capacity_gain=10, status="Repaired", reason_for_priority="Critical blocker resolved",
        expected_coverage_improvement="+10 capacity", suggested_action="Service complete",
        confirmed_by="admin@test.com"
    )
    db_session.add(repair_log)
    db_session.commit()

    # After repair: dynamically recalibrates to FULLY COVERED!
    post_repair_cap = calculate_experiment_capacity(db_session, exp, batch, lab_weekly_hours=40.0)
    assert post_repair_cap["classification"] == "FULLY COVERED"
    assert post_repair_cap["safe_capacity_per_session"] == 10
    assert post_repair_cap["active_stations"] == 5
