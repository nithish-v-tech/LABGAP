export type UserRole = 'admin' | 'faculty' | 'student' | 'hod';

export interface UserProfile {
  id: number;
  email: string;
  full_name: string;
  role: UserRole;
  department_id?: number;
  department_name?: string;
  institution_name?: string;
  is_active: boolean;
  faculty_id?: number;
  faculty_code?: string;
  assigned_laboratory_id?: number;
  student_id?: number;
  student_id_number?: string;
  batch_id?: number;
  batch_code?: string;
}

export interface Laboratory {
  id: number;
  department_id: number;
  code: string;
  name: string;
  location: string;
  max_student_capacity: number;
  working_days: string;
  open_time: string;
  close_time: string;
  assigned_faculty_id?: number;
  assigned_faculty_name?: string;
  equipment_count?: number;
  experiment_count?: number;
}

export interface Equipment {
  id: number;
  laboratory_id: number;
  laboratory_name?: string;
  equipment_code: string;
  name: string;
  description?: string;
  total_quantity: number;
  functional_quantity: number;
  partially_functional_quantity: number;
  damaged_quantity: number;
  under_maintenance_quantity: number;
  available_quantity: number;
  maintenance_status: string;
  repair_status: string;
  associated_experiments_count?: number;
}

export interface ExperimentEquipmentRequirement {
  equipment_id: number;
  equipment_code: string;
  equipment_name: string;
  quantity_required: number;
  functional_available: number;
  damaged?: number;
  is_critical: boolean;
}

export interface Experiment {
  id: number;
  experiment_code: string;
  name: string;
  description?: string;
  laboratory_id: number;
  laboratory_name?: string;
  practical_competency: string;
  equipment_quantity_per_session: number;
  students_per_unit: number;
  min_safe_batch_size: number;
  max_safe_batch_size: number;
  duration_hours: number;
  required_sessions: number;
  completion_criteria: string;
  coverage_classification?: 'FULLY COVERED' | 'PARTIALLY COVERED' | 'NOT COVERED';
  safe_capacity_per_session?: number;
  equipment_shortage?: number;
  reason?: string;
  equipment_requirements?: ExperimentEquipmentRequirement[];
}

export interface StudentBatch {
  id: number;
  department_id: number;
  laboratory_id?: number;
  laboratory_name?: string;
  batch_code: string;
  batch_name: string;
  number_of_students: number;
  assigned_faculty_id?: number;
  assigned_faculty_name?: string;
  assigned_experiments?: Array<{ id: number; name: string; code: string }>;
}

export interface Student {
  id: number;
  student_id_number: string;
  name: string;
  email: string;
  department_id: number;
  batch_id?: number;
  batch_code?: string;
  batch_name?: string;
  verified_completions_count?: number;
}

export interface Faculty {
  id: number;
  faculty_code: string;
  name: string;
  email: string;
  department_id: number;
  assigned_laboratory_id?: number;
  assigned_laboratory_name?: string;
  assigned_batches_count?: number;
  pending_verifications_count?: number;
}

export interface CoverageAnalysisResult {
  experiment_id: number;
  experiment_code: string;
  experiment_name: string;
  laboratory_id: number;
  laboratory_name: string;
  batch_id: number;
  batch_code: string;
  batch_name: string;
  batch_size: number;
  classification: 'FULLY COVERED' | 'PARTIALLY COVERED' | 'NOT COVERED';
  active_stations: number;
  safe_capacity_per_session: number;
  available_capacity: number;
  required_capacity: number;
  equipment_shortage: number;
  time_required_hours: number;
  time_shortage_hours: number;
  students_affected: number;
  bottleneck_equipment?: string;
  reason: string;
  verified_completions: number;
  remaining_learning_gap: number;
  gap_percentage: number;
}

export interface CompletionRecord {
  id: number;
  student_id: number;
  student_name: string;
  student_id_number: string;
  experiment_id: number;
  experiment_name: string;
  experiment_code: string;
  batch_id: number;
  batch_code: string;
  participation_status: 'Not started' | 'Participated' | 'Partially completed' | 'Completed';
  verification_status: 'Pending' | 'Verified' | 'Rejected';
  is_verified_competent: boolean;
  instructor_id?: number;
  instructor_name?: string;
  verification_timestamp?: string;
  assessment_notes?: string;
  created_at: string;
}

export interface ScheduleItem {
  id: number;
  session_number: number;
  date: string;
  start_time: string;
  end_time: string;
  experiment_id: number;
  experiment_code: string;
  experiment_name: string;
  batch_id: number;
  batch_code: string;
  laboratory_id: number;
  laboratory_name: string;
  faculty_id?: number;
  faculty_name?: string;
  student_capacity: number;
  expected_students: number;
  remaining_learning_gap: number;
  status: string;
}

export interface RepairRecommendation {
  equipment_id: number;
  equipment_code: string;
  equipment_name: string;
  laboratory_id: number;
  laboratory_name: string;
  priority: 'Critical' | 'High' | 'Medium' | 'Low';
  current_condition: string;
  total_quantity: number;
  functional_quantity: number;
  damaged_quantity: number;
  under_maintenance_quantity: number;
  partially_functional_quantity: number;
  repairable_units: number;
  affected_experiments_count: number;
  affected_students_count: number;
  potential_capacity_gain: number;
  reason_for_priority: string;
  expected_coverage_improvement: string;
  suggested_action: string;
  repair_status: string;
}

export interface DashboardSummary {
  total_laboratories: number;
  total_experiments: number;
  total_students: number;
  total_batches: number;
  total_equipment_units: number;
  functional_equipment: number;
  partially_functional: number;
  damaged_equipment: number;
  under_maintenance: number;
  fully_covered_experiments: number;
  partially_covered_experiments: number;
  not_covered_experiments: number;
  total_verified_competencies: number;
  total_practical_learning_gap: number;
  equipment_utilization_rate: number;
  condition_distribution: Array<{ name: string; value: number; color: string }>;
  coverage_distribution: Array<{ name: string; count: number; color: string }>;
}
