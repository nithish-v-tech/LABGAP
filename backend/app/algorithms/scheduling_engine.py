import datetime
import math
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from app.database.models import (
    Experiment, StudentBatch, Laboratory, Faculty, Equipment,
    ExperimentEquipment, Schedule, CompletionRecord, Student, BatchExperiment
)
from app.algorithms.capacity_engine import calculate_experiment_capacity

# Standard operational rotation slots strictly within institution hours (09:00 - 17:00)
# Guarantees that every generated session stays within configured laboratory hours
STANDARD_TIME_SLOTS = [
    ("09:00", "11:00"),
    ("11:15", "13:15"),
    ("14:00", "16:00")
]

def check_slot_conflicts(
    db: Session,
    date_str: str,
    slot_start: str,
    slot_end: str,
    lab: Laboratory,
    faculty: Optional[Faculty],
    batch: StudentBatch,
    experiment: Experiment,
    expected_students: int,
    in_memory_schedules: List[Dict[str, Any]]
) -> tuple[bool, Optional[str]]:
    """
    Validates all physical constraints for a proposed session:
    1. Laboratory operating hours (lab.open_time to lab.close_time).
    2. Laboratory room occupancy (no double booking of the lab).
    3. Faculty availability (faculty cannot instruct two concurrent sessions).
    4. Student cohort availability (batch cannot attend two concurrent sessions).
    5. Shared equipment inventory limit (concurrent sessions must not exceed functional units).
    """
    lab_open = lab.open_time if (lab and lab.open_time) else "09:00"
    lab_close = lab.close_time if (lab and lab.close_time) else "17:00"

    # Constraint 1: Operating Hours
    if slot_start < lab_open or slot_end > lab_close:
        return True, f"Slot {slot_start}-{slot_end} falls outside laboratory operating hours ({lab_open}-{lab_close})"

    # Combine database schedules with in-memory schedules planned in current batch
    all_active = []
    db_schedules = db.query(Schedule).filter(
        Schedule.date == date_str,
        Schedule.start_time == slot_start,
        Schedule.status != "Cancelled"
    ).all()
    for s in db_schedules:
        all_active.append({
            "laboratory_id": s.laboratory_id,
            "faculty_id": s.faculty_id,
            "batch_id": s.batch_id,
            "experiment_id": s.experiment_id,
            "expected_students": s.expected_students
        })
    for s in in_memory_schedules:
        if s.get("date") == date_str and s.get("start_time") == slot_start:
            all_active.append({
                "laboratory_id": s.get("laboratory_id"),
                "faculty_id": s.get("faculty_id"),
                "batch_id": s.get("batch_id"),
                "experiment_id": s.get("experiment_id"),
                "expected_students": s.get("expected_students", 0)
            })

    # Constraint 2: Laboratory Occupancy
    for act in all_active:
        if act["laboratory_id"] == lab.id:
            return True, f"Laboratory '{lab.name}' is already occupied during this time slot"

    # Constraint 3: Faculty Schedule Conflict
    if faculty:
        for act in all_active:
            if act.get("faculty_id") and act["faculty_id"] == faculty.id:
                return True, f"Faculty instructor '{faculty.name}' is already assigned to another session"

    # Constraint 4: Batch Availability Conflict
    for act in all_active:
        if act.get("batch_id") and act["batch_id"] == batch.id:
            return True, f"Student cohort '{batch.batch_code}' is already scheduled in another laboratory"

    # Constraint 5: Shared Equipment Concurrency Limit
    # Calculate required equipment for the proposed session
    students_per_unit = experiment.students_per_unit or 2
    stations_needed = math.ceil(expected_students / students_per_unit) if students_per_unit > 0 else 1

    proposed_requirements = db.query(ExperimentEquipment).filter(
        ExperimentEquipment.experiment_id == experiment.id
    ).all()

    for req in proposed_requirements:
        eq = db.query(Equipment).filter(Equipment.id == req.equipment_id).first()
        if not eq:
            continue

        needed_units = stations_needed * req.quantity_required
        functional_total = eq.functional_quantity

        # Count units of this specific equipment committed by other concurrent sessions
        committed_units = 0
        for act in all_active:
            other_exp_id = act.get("experiment_id")
            if not other_exp_id:
                continue
            other_reqs = db.query(ExperimentEquipment).filter(
                ExperimentEquipment.experiment_id == other_exp_id,
                ExperimentEquipment.equipment_id == eq.id
            ).all()
            for o_req in other_reqs:
                other_exp = db.query(Experiment).filter(Experiment.id == other_exp_id).first()
                other_spu = (other_exp.students_per_unit if other_exp else 2) or 2
                other_stations = math.ceil(act.get("expected_students", 0) / other_spu)
                committed_units += (other_stations * o_req.quantity_required)

        if (committed_units + needed_units) > functional_total:
            return True, (
                f"Shared equipment capacity exceeded for '{eq.name}': "
                f"Needs {needed_units} units, {committed_units} already committed concurrently, "
                f"total functional units: {functional_total}"
            )

    return False, None


def generate_optimized_schedule(
    db: Session,
    experiment_id: int,
    batch_id: int,
    start_date: str = None
) -> Dict[str, Any]:
    """
    Constraint-based scheduling algorithm for a single experiment-batch pair.
    Generates feasible student rotation sessions without double booking labs,
    faculty, batch cohorts, or exceeding safe equipment capacity and operating hours.
    """
    experiment = db.query(Experiment).filter(Experiment.id == experiment_id).first()
    batch = db.query(StudentBatch).filter(StudentBatch.id == batch_id).first()

    if not experiment or not batch:
        return {"error": "Experiment or Batch not found", "schedules": []}

    lab = experiment.laboratory
    if not lab:
        return {"error": "Experiment has no assigned laboratory", "schedules": []}

    # Step 1: Calculate capacity & coverage
    capacity_info = calculate_experiment_capacity(db, experiment, batch)
    if capacity_info["classification"] == "NOT COVERED":
        return {
            "success": False,
            "status": "INFEASIBLE",
            "message": f"Cannot generate schedule: {capacity_info['reason']}",
            "bottleneck": capacity_info["bottleneck_equipment"],
            "equipment_shortage": capacity_info["equipment_shortage"],
            "schedules": []
        }

    session_capacity = capacity_info["safe_capacity_per_session"]
    if session_capacity <= 0:
        return {
            "success": False,
            "status": "INFEASIBLE",
            "message": "Safe session capacity is zero.",
            "schedules": []
        }

    # Step 2: Identify students requiring practical completion
    assigned_students = db.query(Student).filter(Student.batch_id == batch.id).all()
    assigned_student_ids = [s.id for s in assigned_students]

    verified_records = db.query(CompletionRecord).filter(
        CompletionRecord.experiment_id == experiment.id,
        CompletionRecord.student_id.in_(assigned_student_ids),
        CompletionRecord.participation_status == "Completed",
        CompletionRecord.verification_status == "Verified"
    ).all()
    verified_ids = set(r.student_id for r in verified_records)

    unverified_students = [s for s in assigned_students if s.id not in verified_ids]
    unverified_count = len(unverified_students)

    if unverified_count == 0:
        target_student_count = batch.number_of_students
    else:
        target_student_count = unverified_count

    required_sessions = math.ceil(target_student_count / session_capacity)

    # Step 3: Find available faculty
    faculty = None
    if batch.assigned_faculty_id:
        faculty = db.query(Faculty).filter(Faculty.id == batch.assigned_faculty_id).first()
    if not faculty and lab.assigned_faculty_id:
        faculty = db.query(Faculty).filter(Faculty.id == lab.assigned_faculty_id).first()
    if not faculty:
        faculty = db.query(Faculty).first()

    # Step 4: Schedule rotation sessions respecting constraints
    base_date = datetime.date.today() + datetime.timedelta(days=1)
    if start_date:
        try:
            base_date = datetime.datetime.strptime(start_date, "%Y-%m-%d").date()
        except ValueError:
            pass

    generated_sessions: List[Dict[str, Any]] = []
    current_day_offset = 0
    slot_index = 0
    sessions_allocated = 0
    students_remaining = target_student_count

    # Max search horizon: 21 days
    while sessions_allocated < required_sessions and current_day_offset < 21:
        sched_date = base_date + datetime.timedelta(days=current_day_offset)
        # Skip Sundays (weekday 6)
        if sched_date.weekday() == 6:
            current_day_offset += 1
            slot_index = 0
            continue

        date_str = sched_date.strftime("%Y-%m-%d")

        while slot_index < len(STANDARD_TIME_SLOTS) and sessions_allocated < required_sessions:
            start_t, end_t = STANDARD_TIME_SLOTS[slot_index]
            assigned_count = min(students_remaining, session_capacity)

            conflict, conflict_reason = check_slot_conflicts(
                db=db,
                date_str=date_str,
                slot_start=start_t,
                slot_end=end_t,
                lab=lab,
                faculty=faculty,
                batch=batch,
                experiment=experiment,
                expected_students=assigned_count,
                in_memory_schedules=generated_sessions
            )

            if not conflict:
                sessions_allocated += 1
                students_remaining = max(0, students_remaining - assigned_count)

                session_dict = {
                    "session_number": sessions_allocated,
                    "date": date_str,
                    "start_time": start_t,
                    "end_time": end_t,
                    "laboratory_id": lab.id,
                    "laboratory_name": lab.name,
                    "experiment_id": experiment.id,
                    "experiment_name": experiment.name,
                    "experiment_code": experiment.experiment_code,
                    "batch_id": batch.id,
                    "batch_code": batch.batch_code,
                    "faculty_id": faculty.id if faculty else None,
                    "faculty_name": faculty.name if faculty else "Unassigned",
                    "student_capacity": session_capacity,
                    "expected_students": assigned_count,
                    "remaining_learning_gap": students_remaining,
                    "status": "Scheduled"
                }
                generated_sessions.append(session_dict)

            slot_index += 1

        slot_index = 0
        current_day_offset += 1

    if sessions_allocated < required_sessions:
        return {
            "success": False,
            "status": "PARTIALLY_SCHEDULED",
            "message": f"Only {sessions_allocated} of {required_sessions} sessions could be scheduled within 21-day window due to constraints.",
            "schedules": generated_sessions,
            "unassigned_students": students_remaining
        }

    return {
        "success": True,
        "status": "FEASIBLE",
        "message": f"Successfully planned {sessions_allocated} rotation session(s) accommodating {target_student_count} student(s) with zero schedule conflicts strictly within laboratory operating hours ({lab.open_time or '09:00'}-{lab.close_time or '17:00'}).",
        "schedules": generated_sessions,
        "unassigned_students": 0
    }


def auto_allocate_cohort_curriculum(
    db: Session,
    batch_ids: Optional[List[int]] = None,
    start_date: Optional[str] = None,
    clear_existing: bool = False
) -> Dict[str, Any]:
    """
    Automated Multi-Batch / Multi-Experiment Lab Allocation Engine.
    Allocates complete curricula across student batches and laboratory facilities.
    Enforces laboratory operating hours, capacity limits, equipment availability,
    faculty workload, and eliminates overlaps across the campus.
    """
    if clear_existing:
        if batch_ids:
            db.query(Schedule).filter(Schedule.batch_id.in_(batch_ids)).delete(synchronize_session=False)
        else:
            db.query(Schedule).delete(synchronize_session=False)
        db.commit()

    # Query target batches
    batch_query = db.query(StudentBatch)
    if batch_ids:
        batch_query = batch_query.filter(StudentBatch.id.in_(batch_ids))
    batches = batch_query.all()

    if not batches:
        return {
            "success": False,
            "message": "No student cohorts found for auto-allocation.",
            "total_batches_processed": 0,
            "total_sessions_allocated": 0,
            "total_students_accommodated": 0,
            "batches": [],
            "schedules": []
        }

    base_date = datetime.date.today() + datetime.timedelta(days=1)
    if start_date:
        try:
            base_date = datetime.datetime.strptime(start_date, "%Y-%m-%d").date()
        except ValueError:
            pass

    overall_sessions: List[Dict[str, Any]] = []
    batch_reports = []
    total_students_accommodated = 0

    for batch in batches:
        # Find assigned experiments
        batch_links = db.query(BatchExperiment).filter(BatchExperiment.batch_id == batch.id).all()
        experiment_ids = [l.experiment_id for l in batch_links]

        # If no explicit links, find all experiments belonging to batch's laboratory or department
        if not experiment_ids:
            if batch.laboratory_id:
                exps = db.query(Experiment).filter(Experiment.laboratory_id == batch.laboratory_id).all()
            else:
                labs = db.query(Laboratory).filter(Laboratory.department_id == batch.department_id).all()
                lab_ids = [l.id for l in labs]
                exps = db.query(Experiment).filter(Experiment.laboratory_id.in_(lab_ids)).all()
            experiment_ids = [e.id for e in exps]

        batch_report = {
            "batch_id": batch.id,
            "batch_code": batch.batch_code,
            "batch_name": batch.batch_name,
            "number_of_students": batch.number_of_students,
            "assigned_experiments_count": len(experiment_ids),
            "scheduled_experiments": [],
            "bottlenecks": []
        }

        for exp_id in experiment_ids:
            exp = db.query(Experiment).filter(Experiment.id == exp_id).first()
            if not exp:
                continue

            lab = exp.laboratory
            if not lab:
                batch_report["bottlenecks"].append({
                    "experiment_code": exp.experiment_code,
                    "experiment_name": exp.name,
                    "reason": "No laboratory assigned to experiment"
                })
                continue

            # Evaluate capacity & coverage
            cap = calculate_experiment_capacity(db, exp, batch)
            if cap["classification"] == "NOT COVERED":
                batch_report["bottlenecks"].append({
                    "experiment_code": exp.experiment_code,
                    "experiment_name": exp.name,
                    "reason": cap.get("reason", "Zero functional equipment"),
                    "bottleneck_equipment": cap.get("bottleneck_equipment")
                })
                continue

            safe_cap = cap["safe_capacity_per_session"]
            if safe_cap <= 0:
                continue

            # Calculate remaining learning gap (unverified students)
            students = db.query(Student).filter(Student.batch_id == batch.id).all()
            student_ids = [s.id for s in students]
            verified = db.query(CompletionRecord).filter(
                CompletionRecord.experiment_id == exp.id,
                CompletionRecord.student_id.in_(student_ids),
                CompletionRecord.participation_status == "Completed",
                CompletionRecord.verification_status == "Verified"
            ).all()
            unverified_count = len(students) - len(verified)
            if unverified_count <= 0:
                unverified_count = batch.number_of_students

            req_sessions = math.ceil(unverified_count / safe_cap)

            faculty = None
            if batch.assigned_faculty_id:
                faculty = db.query(Faculty).filter(Faculty.id == batch.assigned_faculty_id).first()
            if not faculty and lab.assigned_faculty_id:
                faculty = db.query(Faculty).filter(Faculty.id == lab.assigned_faculty_id).first()
            if not faculty:
                faculty = db.query(Faculty).first()

            # Schedule sessions across time horizon
            sessions_allocated = 0
            students_remaining = unverified_count
            current_day_offset = 0
            slot_idx = 0

            while sessions_allocated < req_sessions and current_day_offset < 28:
                sched_date = base_date + datetime.timedelta(days=current_day_offset)
                if sched_date.weekday() == 6:  # Skip Sundays
                    current_day_offset += 1
                    slot_idx = 0
                    continue

                date_str = sched_date.strftime("%Y-%m-%d")

                while slot_idx < len(STANDARD_TIME_SLOTS) and sessions_allocated < req_sessions:
                    s_start, s_end = STANDARD_TIME_SLOTS[slot_idx]
                    count_to_assign = min(students_remaining, safe_cap)

                    conflict, _ = check_slot_conflicts(
                        db=db,
                        date_str=date_str,
                        slot_start=s_start,
                        slot_end=s_end,
                        lab=lab,
                        faculty=faculty,
                        batch=batch,
                        experiment=exp,
                        expected_students=count_to_assign,
                        in_memory_schedules=overall_sessions
                    )

                    if not conflict:
                        sessions_allocated += 1
                        students_remaining = max(0, students_remaining - count_to_assign)
                        total_students_accommodated += count_to_assign

                        sess_entry = {
                            "session_number": sessions_allocated,
                            "date": date_str,
                            "start_time": s_start,
                            "end_time": s_end,
                            "laboratory_id": lab.id,
                            "laboratory_name": lab.name,
                            "experiment_id": exp.id,
                            "experiment_name": exp.name,
                            "experiment_code": exp.experiment_code,
                            "batch_id": batch.id,
                            "batch_code": batch.batch_code,
                            "faculty_id": faculty.id if faculty else None,
                            "faculty_name": faculty.name if faculty else "Unassigned",
                            "student_capacity": safe_cap,
                            "expected_students": count_to_assign,
                            "remaining_learning_gap": students_remaining,
                            "status": "Scheduled"
                        }
                        overall_sessions.append(sess_entry)

                        # Persist to database immediately
                        db_sched = Schedule(
                            experiment_id=exp.id,
                            batch_id=batch.id,
                            laboratory_id=lab.id,
                            faculty_id=faculty.id if faculty else None,
                            session_number=sessions_allocated,
                            date=date_str,
                            start_time=s_start,
                            end_time=s_end,
                            student_capacity=safe_cap,
                            expected_students=count_to_assign,
                            remaining_learning_gap=students_remaining,
                            status="Scheduled"
                        )
                        db.add(db_sched)

                    slot_idx += 1

                slot_idx = 0
                current_day_offset += 1

            batch_report["scheduled_experiments"].append({
                "experiment_code": exp.experiment_code,
                "experiment_name": exp.name,
                "sessions_scheduled": sessions_allocated,
                "sessions_required": req_sessions,
                "is_fully_scheduled": sessions_allocated >= req_sessions
            })

        batch_reports.append(batch_report)

    db.commit()

    return {
        "success": True,
        "message": f"Automated curriculum allocation completed: {len(overall_sessions)} rotation sessions successfully scheduled across {len(batches)} student cohort(s).",
        "total_batches_processed": len(batches),
        "total_sessions_allocated": len(overall_sessions),
        "total_students_accommodated": total_students_accommodated,
        "batches": batch_reports,
        "schedules": overall_sessions
    }
