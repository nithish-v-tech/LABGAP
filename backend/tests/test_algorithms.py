import pytest
import math
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.database.connection import Base
from app.database.models import (
    Institution, Department, Role, User, Laboratory, Faculty,
    StudentBatch, Student, Equipment, Experiment, ExperimentEquipment,
    BatchExperiment, CompletionRecord, Schedule
)
from app.algorithms.capacity_engine import calculate_experiment_capacity
from app.algorithms.gap_analyzer import calculate_student_learning_gap
from app.algorithms.scheduling_engine import generate_optimized_schedule
from app.algorithms.repair_engine import evaluate_equipment_repairs

# In-memory SQLite for isolated algorithm testing
@pytest.fixture
def db_session():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(bind=engine)
    session = Session()

    inst = Institution(name="Test Inst", code="T1")
    session.add(inst)
    session.flush()

    dept = Department(name="Test Dept", code="TD1", institution_id=inst.id)
    session.add(dept)
    session.flush()

    lab = Laboratory(
        name="Electronics Lab", code="L1", location="Room 101",
        max_student_capacity=30, department_id=dept.id
    )
    session.add(lab)
    session.flush()

    yield session
    session.close()

def test_coverage_classification_fully_covered(db_session):
    lab = db_session.query(Laboratory).first()
    # Batch with 20 students
    batch = StudentBatch(
        batch_code="B1", batch_name="Batch 1", department_id=lab.department_id,
        number_of_students=20, laboratory_id=lab.id
    )
    db_session.add(batch)
    db_session.flush()

    # Equipment with 10 functional units
    eq = Equipment(
        laboratory_id=lab.id, equipment_code="EQ-OSC", name="Oscilloscope",
        total_quantity=10, functional_quantity=10, partially_functional_quantity=0,
        damaged_quantity=0, under_maintenance_quantity=0
    )
    db_session.add(eq)
    db_session.flush()

    exp = Experiment(
        laboratory_id=lab.id, experiment_code="EXP-01", name="Op-Amp",
        practical_competency="Analog Circuits", duration_hours=2.0,
        students_per_unit=2, min_safe_batch_size=4, max_safe_batch_size=30,
        completion_criteria="Viva passed"
    )
    db_session.add(exp)
    db_session.flush()

    # Link: 1 unit of EQ-OSC per station
    db_session.add(ExperimentEquipment(experiment_id=exp.id, equipment_id=eq.id, quantity_required=1))
    db_session.commit()

    res = calculate_experiment_capacity(db_session, exp, batch, lab_weekly_hours=40.0)
    assert res["classification"] == "FULLY COVERED"
    assert res["active_stations"] == 10
    assert res["safe_capacity_per_session"] == 20  # 10 stations * 2 students = 20 students
    assert res["required_sessions"] == 1
    assert res["equipment_shortage"] == 0

def test_coverage_classification_not_covered_due_to_damaged_equipment(db_session):
    lab = db_session.query(Laboratory).first()
    batch = StudentBatch(
        batch_code="B2", batch_name="Batch 2", department_id=lab.department_id,
        number_of_students=25, laboratory_id=lab.id
    )
    db_session.add(batch)
    db_session.flush()

    # Equipment: 4 total, 0 functional, 3 damaged, 1 under maintenance
    eq = Equipment(
        laboratory_id=lab.id, equipment_code="EQ-MOTOR", name="3-Phase Motor",
        total_quantity=4, functional_quantity=0, partially_functional_quantity=0,
        damaged_quantity=3, under_maintenance_quantity=1
    )
    db_session.add(eq)
    db_session.flush()

    exp = Experiment(
        laboratory_id=lab.id, experiment_code="EXP-MOTOR", name="Motor Test",
        practical_competency="AC Machines", duration_hours=3.0,
        students_per_unit=3, min_safe_batch_size=6, max_safe_batch_size=24,
        completion_criteria="Viva passed"
    )
    db_session.add(exp)
    db_session.flush()

    db_session.add(ExperimentEquipment(experiment_id=exp.id, equipment_id=eq.id, quantity_required=1))
    db_session.commit()

    res = calculate_experiment_capacity(db_session, exp, batch, lab_weekly_hours=40.0)
    assert res["classification"] == "NOT COVERED"
    assert res["active_stations"] == 0
    assert res["safe_capacity_per_session"] == 0
    assert res["students_affected"] == 25
    assert "Zero functional units" in res["reason"]

def test_learning_gap_requires_verified_completion_not_attendance(db_session):
    lab = db_session.query(Laboratory).first()
    batch = StudentBatch(
        batch_code="B3", batch_name="Batch 3", department_id=lab.department_id,
        number_of_students=4, laboratory_id=lab.id
    )
    db_session.add(batch)
    db_session.flush()

    exp = Experiment(
        laboratory_id=lab.id, experiment_code="EXP-GAP", name="Gap Test Exp",
        practical_competency="Logic", duration_hours=2.0, students_per_unit=2,
        min_safe_batch_size=2, max_safe_batch_size=20, completion_criteria="Viva"
    )
    db_session.add(exp)
    db_session.flush()

    students = []
    for i in range(1, 5):
        s = Student(
            student_id_number=f"S{i}", name=f"Student {i}", email=f"s{i}@test.com",
            department_id=lab.department_id, batch_id=batch.id
        )
        db_session.add(s)
        students.append(s)
    db_session.flush()

    # Student 1: Participated but Verification is Pending (Attendance only - should NOT count!)
    db_session.add(CompletionRecord(
        student_id=students[0].id, experiment_id=exp.id, batch_id=batch.id,
        participation_status="Participated", verification_status="Pending"
    ))
    # Student 2: Completed and Verified (MUST count!)
    db_session.add(CompletionRecord(
        student_id=students[1].id, experiment_id=exp.id, batch_id=batch.id,
        participation_status="Completed", verification_status="Verified"
    ))
    # Student 3: Partially completed (does NOT count)
    db_session.add(CompletionRecord(
        student_id=students[2].id, experiment_id=exp.id, batch_id=batch.id,
        participation_status="Partially completed", verification_status="Pending"
    ))
    # Student 4: Not started
    db_session.commit()

    gap_res = calculate_student_learning_gap(db_session, exp.id, batch.id)
    assert gap_res["total_assigned"] == 4
    assert gap_res["verified_completed"] == 1  # Only Student 2 counts
    assert gap_res["unverified_learning_gap"] == 3  # Students 1, 3, 4 are part of gap!
    assert gap_res["gap_percentage"] == 75.0

def test_repair_recommendation_prioritizes_critical_blockers(db_session):
    lab = db_session.query(Laboratory).first()
    batch = StudentBatch(
        batch_code="B4", batch_name="Batch 4", department_id=lab.department_id,
        number_of_students=35, laboratory_id=lab.id
    )
    db_session.add(batch)
    db_session.flush()

    # Critical broken equipment (causes 0 functional stations for 35 students)
    eq_broken = Equipment(
        laboratory_id=lab.id, equipment_code="EQ-CRIT", name="Critical Generator",
        total_quantity=5, functional_quantity=0, partially_functional_quantity=0,
        damaged_quantity=5, under_maintenance_quantity=0
    )
    db_session.add(eq_broken)

    # Minor broken equipment
    eq_minor = Equipment(
        laboratory_id=lab.id, equipment_code="EQ-MIN", name="Minor Meter",
        total_quantity=10, functional_quantity=9, partially_functional_quantity=0,
        damaged_quantity=1, under_maintenance_quantity=0
    )
    db_session.add(eq_minor)
    db_session.flush()

    exp = Experiment(
        laboratory_id=lab.id, experiment_code="EXP-BLOCK", name="Blocked Exp",
        practical_competency="Power", duration_hours=3.0, students_per_unit=2,
        min_safe_batch_size=4, max_safe_batch_size=30, completion_criteria="Viva"
    )
    db_session.add(exp)
    db_session.flush()

    db_session.add(ExperimentEquipment(experiment_id=exp.id, equipment_id=eq_broken.id, quantity_required=1))
    db_session.add(BatchExperiment(batch_id=batch.id, experiment_id=exp.id))
    db_session.commit()

    repairs = evaluate_equipment_repairs(db_session)
    assert len(repairs) >= 1
    top_repair = repairs[0]
    assert top_repair["equipment_id"] == eq_broken.id
    assert top_repair["priority"] == "Critical"
    assert top_repair["potential_capacity_gain"] > 0
