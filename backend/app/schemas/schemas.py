import datetime
from typing import List, Optional, Any
from pydantic import BaseModel, Field, ConfigDict

# Authentication & Users
class Token(BaseModel):
    access_token: str
    token_type: str
    user: dict

class TokenData(BaseModel):
    email: Optional[str] = None

class LoginRequest(BaseModel):
    email: str
    password: str

class UserResponse(BaseModel):
    id: int
    email: str
    full_name: str
    role: str
    department_id: Optional[int] = None
    is_active: bool

    model_config = ConfigDict(from_attributes=True)

# Laboratory
class LaboratoryBase(BaseModel):
    code: str
    name: str
    location: str
    max_student_capacity: int = 30
    working_days: str = "Monday to Friday"
    open_time: str = "09:00"
    close_time: str = "17:00"
    department_id: int

class LaboratoryCreate(LaboratoryBase):
    assigned_faculty_id: Optional[int] = None

class LaboratoryUpdate(BaseModel):
    name: Optional[str] = None
    location: Optional[str] = None
    max_student_capacity: Optional[int] = None
    working_days: Optional[str] = None
    open_time: Optional[str] = None
    close_time: Optional[str] = None
    assigned_faculty_id: Optional[int] = None

class LaboratoryResponse(LaboratoryBase):
    id: int
    assigned_faculty_id: Optional[int] = None
    created_at: datetime.datetime

    model_config = ConfigDict(from_attributes=True)

# Faculty
class FacultyBase(BaseModel):
    faculty_code: str
    name: str
    email: str
    department_id: int
    assigned_laboratory_id: Optional[int] = None

class FacultyCreate(FacultyBase):
    password: str = "FacultyPassword123!"

class FacultyResponse(FacultyBase):
    id: int
    user_id: int
    created_at: datetime.datetime

    model_config = ConfigDict(from_attributes=True)

# Student Batches
class StudentBatchBase(BaseModel):
    batch_code: str
    batch_name: str
    department_id: int
    laboratory_id: Optional[int] = None
    number_of_students: int = 0
    assigned_faculty_id: Optional[int] = None

class StudentBatchCreate(StudentBatchBase):
    pass

class StudentBatchResponse(StudentBatchBase):
    id: int
    created_at: datetime.datetime

    model_config = ConfigDict(from_attributes=True)

# Students
class StudentBase(BaseModel):
    student_id_number: str
    name: str
    email: str
    department_id: int
    batch_id: Optional[int] = None

class StudentCreate(StudentBase):
    password: str = "StudentPassword123!"

class StudentResponse(StudentBase):
    id: int
    user_id: Optional[int] = None
    created_at: datetime.datetime

    model_config = ConfigDict(from_attributes=True)

# Equipment
class EquipmentBase(BaseModel):
    laboratory_id: int
    equipment_code: str
    name: str
    description: Optional[str] = None
    total_quantity: int = Field(..., ge=0)
    functional_quantity: int = Field(..., ge=0)
    partially_functional_quantity: int = Field(default=0, ge=0)
    damaged_quantity: int = Field(default=0, ge=0)
    under_maintenance_quantity: int = Field(default=0, ge=0)
    maintenance_status: str = "Normal"
    repair_status: str = "None"

class EquipmentCreate(EquipmentBase):
    pass

class EquipmentUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    laboratory_id: Optional[int] = None
    total_quantity: Optional[int] = None
    functional_quantity: Optional[int] = None
    partially_functional_quantity: Optional[int] = None
    damaged_quantity: Optional[int] = None
    under_maintenance_quantity: Optional[int] = None
    maintenance_status: Optional[str] = None
    repair_status: Optional[str] = None

class EquipmentResponse(EquipmentBase):
    id: int
    created_at: datetime.datetime
    updated_at: datetime.datetime

    model_config = ConfigDict(from_attributes=True)

# Experiments
class ExperimentEquipmentReq(BaseModel):
    equipment_id: int
    quantity_required: int = 1
    is_critical: bool = True

class ExperimentBase(BaseModel):
    laboratory_id: int
    experiment_code: str
    name: str
    description: Optional[str] = None
    practical_competency: str
    equipment_quantity_per_session: int = 1
    students_per_unit: int = 2
    min_safe_batch_size: int = 4
    max_safe_batch_size: int = 30
    duration_hours: float = 2.0
    required_sessions: int = 1
    completion_criteria: str

class ExperimentCreate(ExperimentBase):
    equipment_requirements: Optional[List[ExperimentEquipmentReq]] = []

class ExperimentUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    laboratory_id: Optional[int] = None
    practical_competency: Optional[str] = None
    equipment_quantity_per_session: Optional[int] = None
    students_per_unit: Optional[int] = None
    min_safe_batch_size: Optional[int] = None
    max_safe_batch_size: Optional[int] = None
    duration_hours: Optional[float] = None
    required_sessions: Optional[int] = None
    completion_criteria: Optional[str] = None
    equipment_requirements: Optional[List[ExperimentEquipmentReq]] = None

class ExperimentResponse(ExperimentBase):
    id: int
    created_at: datetime.datetime
    equipment_requirements: Optional[List[Any]] = []

    model_config = ConfigDict(from_attributes=True)

# Completion & Verification
class CompletionRecordCreate(BaseModel):
    student_id: int
    experiment_id: int
    batch_id: int
    participation_status: str = "Participated"  # Not started, Participated, Partially completed, Completed
    assessment_notes: Optional[str] = None

class CompletionRecordVerify(BaseModel):
    verification_status: str  # Verified, Rejected, Pending
    assessment_notes: Optional[str] = None

class CompletionRecordResponse(BaseModel):
    id: int
    student_id: int
    student_name: Optional[str] = None
    student_id_number: Optional[str] = None
    experiment_id: int
    experiment_name: Optional[str] = None
    batch_id: int
    batch_code: Optional[str] = None
    participation_status: str
    verification_status: str
    instructor_id: Optional[int] = None
    instructor_name: Optional[str] = None
    verification_timestamp: Optional[datetime.datetime] = None
    assessment_notes: Optional[str] = None
    created_at: datetime.datetime
    updated_at: datetime.datetime

    model_config = ConfigDict(from_attributes=True)

# Schedules
class ScheduleCreateRequest(BaseModel):
    experiment_id: int
    batch_id: int
    start_date: Optional[str] = None

class AutoAllocateRequest(BaseModel):
    batch_ids: Optional[List[int]] = None
    start_date: Optional[str] = None
    clear_existing: Optional[bool] = False

class ApproveAllocationRequest(BaseModel):
    experiment_id: int
    batch_id: int
    laboratory_id: int
    start_date: Optional[str] = None

class ScheduleResponse(BaseModel):
    id: int
    experiment_id: int
    experiment_name: Optional[str] = None
    batch_id: int
    batch_code: Optional[str] = None
    laboratory_id: int
    laboratory_name: Optional[str] = None
    faculty_id: Optional[int] = None
    faculty_name: Optional[str] = None
    session_number: int
    date: str
    start_time: str
    end_time: str
    student_capacity: int
    expected_students: int
    remaining_learning_gap: int
    status: str
    created_at: datetime.datetime

    model_config = ConfigDict(from_attributes=True)

# Repair Confirmation
class RepairConfirmRequest(BaseModel):
    equipment_id: int
    action: str = "mark_repaired"  # mark_repaired, inspect, mark_under_maintenance
    units_to_restore: int = 1
    notes: Optional[str] = None
