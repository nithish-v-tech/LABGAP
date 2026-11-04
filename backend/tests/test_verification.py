import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.database.connection import Base
from app.database.models import (
    Institution, Department, Role, User, Laboratory, Faculty,
    StudentBatch, Student, Experiment, CompletionRecord
)

@pytest.fixture
def setup_data():
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

    role_faculty = Role(name="faculty")
    role_student = Role(name="student")
    session.add_all([role_faculty, role_student])
    session.flush()

    user_fac = User(
        email="fac@test.com", hashed_password="pwd", full_name="Prof Test",
        role_id=role_faculty.id, department_id=dept.id
    )
    user_stu = User(
        email="stu@test.com", hashed_password="pwd", full_name="Student Test",
        role_id=role_student.id, department_id=dept.id
    )
    session.add_all([user_fac, user_stu])
    session.flush()

    fac = Faculty(
        user_id=user_fac.id, department_id=dept.id, faculty_code="FAC-01",
        name="Prof Test", email="fac@test.com"
    )
    session.add(fac)

    batch = StudentBatch(
        batch_code="B-TEST", batch_name="Test Batch", department_id=dept.id, number_of_students=1
    )
    session.add(batch)
    session.flush()

    stu = Student(
        user_id=user_stu.id, student_id_number="STU-001", name="Student Test",
        email="stu@test.com", department_id=dept.id, batch_id=batch.id
    )
    session.add(stu)

    lab = Laboratory(name="Test Lab", code="TL1", location="Room 1", department_id=dept.id)
    session.add(lab)
    session.flush()

    exp = Experiment(
        laboratory_id=lab.id, experiment_code="EXP-VERIFY", name="Verification Exp",
        practical_competency="Precision", duration_hours=2.0, students_per_unit=2,
        min_safe_batch_size=2, max_safe_batch_size=20, completion_criteria="Viva"
    )
    session.add(exp)
    session.commit()

    return {
        "session": session,
        "student": stu,
        "faculty": fac,
        "batch": batch,
        "experiment": exp
    }

def test_record_and_verify_completion(setup_data):
    session = setup_data["session"]
    stu = setup_data["student"]
    exp = setup_data["experiment"]
    batch = setup_data["batch"]
    fac = setup_data["faculty"]

    # 1. Faculty records participation
    rec = CompletionRecord(
        student_id=stu.id,
        experiment_id=exp.id,
        batch_id=batch.id,
        participation_status="Completed",
        verification_status="Pending",
        instructor_id=fac.id,
        assessment_notes="Circuit working."
    )
    session.add(rec)
    session.commit()

    assert rec.participation_status == "Completed"
    assert rec.verification_status == "Pending"
    # Not yet counted as verified competency
    assert not (rec.participation_status == "Completed" and rec.verification_status == "Verified")

    # 2. Faculty verifies
    rec.verification_status = "Verified"
    session.commit()

    # Now counts as verified competency!
    assert (rec.participation_status == "Completed" and rec.verification_status == "Verified")

def test_duplicate_verified_completion_prevention(setup_data):
    session = setup_data["session"]
    stu = setup_data["student"]
    exp = setup_data["experiment"]
    batch = setup_data["batch"]
    fac = setup_data["faculty"]

    # Create first verified record
    rec1 = CompletionRecord(
        student_id=stu.id,
        experiment_id=exp.id,
        batch_id=batch.id,
        participation_status="Completed",
        verification_status="Verified",
        instructor_id=fac.id
    )
    session.add(rec1)
    session.commit()

    # Second record with same student and experiment should violate unique constraint
    rec2 = CompletionRecord(
        student_id=stu.id,
        experiment_id=exp.id,
        batch_id=batch.id,
        participation_status="Completed",
        verification_status="Pending"
    )
    session.add(rec2)
    with pytest.raises(Exception):
        session.commit()
    session.rollback()
