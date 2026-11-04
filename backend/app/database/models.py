import datetime
from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, ForeignKey, Text, CheckConstraint, UniqueConstraint
from sqlalchemy.orm import relationship
from app.database.connection import Base

class Institution(Base):
    __tablename__ = "institutions"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    code = Column(String(50), unique=True, nullable=False)
    address = Column(String(255), nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    departments = relationship("Department", back_populates="institution")

class Department(Base):
    __tablename__ = "departments"
    id = Column(Integer, primary_key=True, index=True)
    institution_id = Column(Integer, ForeignKey("institutions.id"), nullable=False)
    name = Column(String(255), nullable=False)
    code = Column(String(50), unique=True, nullable=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    institution = relationship("Institution", back_populates="departments")
    laboratories = relationship("Laboratory", back_populates="department")
    users = relationship("User", back_populates="department")
    batches = relationship("StudentBatch", back_populates="department")
    students = relationship("Student", back_populates="department")

class Role(Base):
    __tablename__ = "roles"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(50), unique=True, nullable=False)  # admin, faculty, student, hod
    description = Column(String(255), nullable=True)

    users = relationship("User", back_populates="role")

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(255), nullable=False)
    role_id = Column(Integer, ForeignKey("roles.id"), nullable=False)
    department_id = Column(Integer, ForeignKey("departments.id"), nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    role = relationship("Role", back_populates="users")
    department = relationship("Department", back_populates="users")
    faculty_profile = relationship("Faculty", back_populates="user", uselist=False)
    student_profile = relationship("Student", back_populates="user", uselist=False)

class Laboratory(Base):
    __tablename__ = "laboratories"
    id = Column(Integer, primary_key=True, index=True)
    department_id = Column(Integer, ForeignKey("departments.id"), nullable=False)
    code = Column(String(50), unique=True, nullable=False)
    name = Column(String(255), nullable=False)
    location = Column(String(255), nullable=False)
    max_student_capacity = Column(Integer, default=30)
    working_days = Column(String(100), default="Monday to Friday")
    open_time = Column(String(20), default="09:00")
    close_time = Column(String(20), default="17:00")
    assigned_faculty_id = Column(Integer, ForeignKey("faculty.id", use_alter=True), nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    department = relationship("Department", back_populates="laboratories")
    equipment_items = relationship("Equipment", back_populates="laboratory")
    experiments = relationship("Experiment", back_populates="laboratory")
    batches = relationship("StudentBatch", back_populates="laboratory")

class Faculty(Base):
    __tablename__ = "faculty"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True, nullable=False)
    department_id = Column(Integer, ForeignKey("departments.id"), nullable=False)
    faculty_code = Column(String(50), unique=True, nullable=False)
    name = Column(String(255), nullable=False)
    email = Column(String(255), nullable=False)
    assigned_laboratory_id = Column(Integer, ForeignKey("laboratories.id", use_alter=True), nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    user = relationship("User", back_populates="faculty_profile")
    verified_records = relationship("CompletionRecord", back_populates="instructor")

class StudentBatch(Base):
    __tablename__ = "student_batches"
    id = Column(Integer, primary_key=True, index=True)
    department_id = Column(Integer, ForeignKey("departments.id"), nullable=False)
    laboratory_id = Column(Integer, ForeignKey("laboratories.id"), nullable=True)
    batch_code = Column(String(50), unique=True, nullable=False)
    batch_name = Column(String(255), nullable=False)
    number_of_students = Column(Integer, default=0)
    assigned_faculty_id = Column(Integer, ForeignKey("faculty.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    department = relationship("Department", back_populates="batches")
    laboratory = relationship("Laboratory", back_populates="batches")
    students = relationship("Student", back_populates="batch")
    batch_experiments = relationship("BatchExperiment", back_populates="batch")

class Student(Base):
    __tablename__ = "students"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True, nullable=True)
    student_id_number = Column(String(50), unique=True, nullable=False)
    name = Column(String(255), nullable=False)
    email = Column(String(255), unique=True, nullable=False)
    department_id = Column(Integer, ForeignKey("departments.id"), nullable=False)
    batch_id = Column(Integer, ForeignKey("student_batches.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    user = relationship("User", back_populates="student_profile")
    department = relationship("Department", back_populates="students")
    batch = relationship("StudentBatch", back_populates="students")
    completions = relationship("CompletionRecord", back_populates="student")

class Equipment(Base):
    __tablename__ = "equipment"
    id = Column(Integer, primary_key=True, index=True)
    laboratory_id = Column(Integer, ForeignKey("laboratories.id"), nullable=False)
    equipment_code = Column(String(50), unique=True, nullable=False)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    total_quantity = Column(Integer, default=0, nullable=False)
    functional_quantity = Column(Integer, default=0, nullable=False)
    partially_functional_quantity = Column(Integer, default=0, nullable=False)
    damaged_quantity = Column(Integer, default=0, nullable=False)
    under_maintenance_quantity = Column(Integer, default=0, nullable=False)
    maintenance_status = Column(String(50), default="Normal")  # Normal, Scheduled, Overdue
    repair_status = Column(String(50), default="None")         # None, Inspection Required, In Repair
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

    laboratory = relationship("Laboratory", back_populates="equipment_items")
    experiment_associations = relationship("ExperimentEquipment", back_populates="equipment")
    repair_records = relationship("RepairRecord", back_populates="equipment")

    __table_args__ = (
        CheckConstraint(
            'total_quantity >= 0 AND functional_quantity >= 0 AND partially_functional_quantity >= 0 AND damaged_quantity >= 0 AND under_maintenance_quantity >= 0',
            name='check_non_negative_quantities'
        ),
    )

class Experiment(Base):
    __tablename__ = "experiments"
    id = Column(Integer, primary_key=True, index=True)
    laboratory_id = Column(Integer, ForeignKey("laboratories.id"), nullable=False)
    experiment_code = Column(String(50), unique=True, nullable=False)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    practical_competency = Column(String(255), nullable=False)
    equipment_quantity_per_session = Column(Integer, default=1, nullable=False)
    students_per_unit = Column(Integer, default=2, nullable=False)
    min_safe_batch_size = Column(Integer, default=4, nullable=False)
    max_safe_batch_size = Column(Integer, default=30, nullable=False)
    duration_hours = Column(Float, default=2.0, nullable=False)
    required_sessions = Column(Integer, default=1, nullable=False)
    completion_criteria = Column(Text, default="Successful circuit assembly, calibrated measurement output and faculty viva verification.")
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    laboratory = relationship("Laboratory", back_populates="experiments")
    equipment_requirements = relationship("ExperimentEquipment", back_populates="experiment", cascade="all, delete-orphan")
    batch_associations = relationship("BatchExperiment", back_populates="experiment")
    completion_records = relationship("CompletionRecord", back_populates="experiment")
    schedules = relationship("Schedule", back_populates="experiment")

class ExperimentEquipment(Base):
    __tablename__ = "experiment_equipment"
    id = Column(Integer, primary_key=True, index=True)
    experiment_id = Column(Integer, ForeignKey("experiments.id"), nullable=False)
    equipment_id = Column(Integer, ForeignKey("equipment.id"), nullable=False)
    quantity_required = Column(Integer, default=1, nullable=False)
    is_critical = Column(Boolean, default=True)

    experiment = relationship("Experiment", back_populates="equipment_requirements")
    equipment = relationship("Equipment", back_populates="experiment_associations")

    __table_args__ = (
        UniqueConstraint('experiment_id', 'equipment_id', name='uq_experiment_equipment'),
    )

class BatchExperiment(Base):
    __tablename__ = "batch_experiments"
    id = Column(Integer, primary_key=True, index=True)
    batch_id = Column(Integer, ForeignKey("student_batches.id"), nullable=False)
    experiment_id = Column(Integer, ForeignKey("experiments.id"), nullable=False)
    assigned_at = Column(DateTime, default=datetime.datetime.utcnow)

    batch = relationship("StudentBatch", back_populates="batch_experiments")
    experiment = relationship("Experiment", back_populates="batch_associations")

    __table_args__ = (
        UniqueConstraint('batch_id', 'experiment_id', name='uq_batch_experiment'),
    )

class LaboratorySession(Base):
    __tablename__ = "laboratory_sessions"
    id = Column(Integer, primary_key=True, index=True)
    experiment_id = Column(Integer, ForeignKey("experiments.id"), nullable=False)
    batch_id = Column(Integer, ForeignKey("student_batches.id"), nullable=False)
    laboratory_id = Column(Integer, ForeignKey("laboratories.id"), nullable=False)
    faculty_id = Column(Integer, ForeignKey("faculty.id"), nullable=True)
    session_code = Column(String(50), unique=True, nullable=False)
    date = Column(String(20), nullable=False)
    start_time = Column(String(10), nullable=False)
    end_time = Column(String(10), nullable=False)
    capacity = Column(Integer, default=10)
    status = Column(String(50), default="Scheduled")  # Scheduled, Completed, Cancelled
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

class CompletionRecord(Base):
    __tablename__ = "completion_records"
    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey("students.id"), nullable=False)
    experiment_id = Column(Integer, ForeignKey("experiments.id"), nullable=False)
    batch_id = Column(Integer, ForeignKey("student_batches.id"), nullable=False)
    session_id = Column(Integer, ForeignKey("laboratory_sessions.id"), nullable=True)
    participation_status = Column(String(50), default="Not started")  # Not started, Participated, Partially completed, Completed
    verification_status = Column(String(50), default="Pending")       # Pending, Verified, Rejected
    instructor_id = Column(Integer, ForeignKey("faculty.id"), nullable=True)
    verification_timestamp = Column(DateTime, nullable=True)
    assessment_notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

    student = relationship("Student", back_populates="completions")
    experiment = relationship("Experiment", back_populates="completion_records")
    instructor = relationship("Faculty", back_populates="verified_records")

    __table_args__ = (
        UniqueConstraint('student_id', 'experiment_id', name='uq_student_experiment_completion'),
    )

class Schedule(Base):
    __tablename__ = "schedules"
    id = Column(Integer, primary_key=True, index=True)
    experiment_id = Column(Integer, ForeignKey("experiments.id"), nullable=False)
    batch_id = Column(Integer, ForeignKey("student_batches.id"), nullable=False)
    laboratory_id = Column(Integer, ForeignKey("laboratories.id"), nullable=False)
    faculty_id = Column(Integer, ForeignKey("faculty.id"), nullable=True)
    session_number = Column(Integer, default=1)
    date = Column(String(20), nullable=False)
    start_time = Column(String(10), nullable=False)
    end_time = Column(String(10), nullable=False)
    student_capacity = Column(Integer, nullable=False)
    expected_students = Column(Integer, nullable=False)
    remaining_learning_gap = Column(Integer, default=0)
    status = Column(String(50), default="Scheduled")  # Scheduled, Executed, Cancelled
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    experiment = relationship("Experiment", back_populates="schedules")

class RepairRecord(Base):
    __tablename__ = "repair_records"
    id = Column(Integer, primary_key=True, index=True)
    equipment_id = Column(Integer, ForeignKey("equipment.id"), nullable=False)
    priority = Column(String(20), nullable=False)  # Critical, High, Medium, Low
    current_condition = Column(String(50), nullable=False)
    affected_experiments_count = Column(Integer, default=0)
    affected_students_count = Column(Integer, default=0)
    equipment_shortage = Column(Integer, default=1)
    potential_capacity_gain = Column(Integer, default=0)
    status = Column(String(50), default="Pending Approval")  # Pending Approval, In Repair, Repaired, Replaced
    reason_for_priority = Column(Text, nullable=False)
    expected_coverage_improvement = Column(Text, nullable=False)
    suggested_action = Column(Text, nullable=False)
    confirmed_by = Column(String(100), nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

    equipment = relationship("Equipment", back_populates="repair_records")

class AnalysisResult(Base):
    __tablename__ = "analysis_results"
    id = Column(Integer, primary_key=True, index=True)
    department_id = Column(Integer, ForeignKey("departments.id"), nullable=False)
    experiment_id = Column(Integer, ForeignKey("experiments.id"), nullable=False)
    batch_id = Column(Integer, ForeignKey("student_batches.id"), nullable=False)
    classification = Column(String(50), nullable=False)  # FULLY COVERED, PARTIALLY COVERED, NOT COVERED
    available_capacity = Column(Integer, nullable=False)
    required_capacity = Column(Integer, nullable=False)
    equipment_shortage = Column(Integer, default=0)
    time_shortage_hours = Column(Float, default=0.0)
    students_affected = Column(Integer, default=0)
    reason = Column(Text, nullable=False)
    verified_completions = Column(Integer, default=0)
    remaining_gap = Column(Integer, default=0)
    calculated_at = Column(DateTime, default=datetime.datetime.utcnow)

class ImportHistory(Base):
    __tablename__ = "import_history"
    id = Column(Integer, primary_key=True, index=True)
    file_name = Column(String(255), nullable=False)
    entity_type = Column(String(50), nullable=False)  # experiments, equipment, students, batches
    total_rows = Column(Integer, default=0)
    successful_rows = Column(Integer, default=0)
    rejected_rows = Column(Integer, default=0)
    error_log = Column(Text, nullable=True)
    imported_at = Column(DateTime, default=datetime.datetime.utcnow)
