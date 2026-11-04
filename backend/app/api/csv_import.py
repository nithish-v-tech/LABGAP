import io
import csv
from typing import List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from fastapi.responses import PlainTextResponse
from sqlalchemy.orm import Session
from app.database.connection import get_db
from app.database.models import (
    Experiment, Equipment, StudentBatch, Student, Laboratory,
    ImportHistory, User
)
from app.security.permissions import require_admin

router = APIRouter(prefix="/csv", tags=["CSV Import & Templates"])

TEMPLATES = {
    "experiments": (
        "experiment_code,name,description,laboratory_code,practical_competency,duration_hours,students_per_unit,min_safe_batch,max_safe_batch,completion_criteria\n"
        "EXP-DEMO-01,Inverting Amplifier Op-Amp,Study operational amplifier inverting configuration,LAB-EC-01,Analog IC Circuit Design,2.0,2,4,30,Calibrated oscilloscope reading and gain verification.\n"
        "EXP-DEMO-02,Synchronous Motor Load Test,Evaluate motor torque and speed characteristics,LAB-PS-01,High-Voltage Electrical Machines,3.0,3,6,24,Torque curve plotting and instructor viva.\n"
    ),
    "equipment": (
        "equipment_code,name,laboratory_code,total_quantity,functional_quantity,partially_functional_quantity,damaged_quantity,under_maintenance_quantity,maintenance_status\n"
        "EQ-DEMO-01,Digital Storage Oscilloscope 100MHz,LAB-EC-01,10,8,0,2,0,Normal\n"
        "EQ-DEMO-02,Dual Regulated DC Power Supply,LAB-EC-01,12,10,1,1,0,Normal\n"
        "EQ-DEMO-03,Three-Phase Squirrel Cage Induction Motor,LAB-PS-01,6,4,0,1,1,Scheduled\n"
    ),
    "students": (
        "student_id_number,name,email,batch_code\n"
        "STU-DEMO-01,Aditi Sharma,aditi.sharma@institution.edu,BATCH-2026-A\n"
        "STU-DEMO-02,Rohan Deshmukh,rohan.deshmukh@institution.edu,BATCH-2026-A\n"
        "STU-DEMO-03,Kavya Sundaram,kavya.sundaram@institution.edu,BATCH-2026-B\n"
    ),
    "batches": (
        "batch_code,batch_name,laboratory_code,number_of_students\n"
        "BATCH-DEMO-A,3rd Year Electrical Section A,LAB-EC-01,25\n"
        "BATCH-DEMO-B,3rd Year Electrical Section B,LAB-PS-01,25\n"
    )
}

@router.get("/template/{entity_type}")
def get_csv_template(entity_type: str):
    if entity_type not in TEMPLATES:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid entity type '{entity_type}'. Available templates: {', '.join(TEMPLATES.keys())}"
        )
    return PlainTextResponse(
        TEMPLATES[entity_type],
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename={entity_type}_template.csv"}
    )

@router.post("/upload/{entity_type}")
async def upload_csv(
    entity_type: str,
    file: UploadFile = File(...),
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    if entity_type not in TEMPLATES:
        raise HTTPException(status_code=400, detail="Unsupported entity type for CSV import")

    contents = await file.read()
    try:
        decoded_text = contents.decode("utf-8-sig")
    except UnicodeDecodeError:
        try:
            decoded_text = contents.decode("latin1")
        except Exception:
            raise HTTPException(status_code=400, detail="Could not decode CSV file. Ensure valid UTF-8 encoding.")

    reader = csv.DictReader(io.StringIO(decoded_text))
    if not reader.fieldnames:
        raise HTTPException(status_code=400, detail="CSV file has empty header row or is invalid.")

    rows = list(reader)
    total_rows = len(rows)
    successful_rows = 0
    rejected_rows = 0
    errors = []

    if total_rows == 0:
        return {
            "entity_type": entity_type,
            "total_rows": 0,
            "successful_rows": 0,
            "rejected_rows": 0,
            "errors": ["File contains headers but zero data rows."]
        }

    for idx, row in enumerate(rows, start=2):  # Line 2 corresponds to first data row
        # Check empty row
        if not any(val.strip() for val in row.values() if val):
            continue

        try:
            if entity_type == "experiments":
                # Validate columns
                required = ["experiment_code", "name", "laboratory_code", "practical_competency"]
                for r in required:
                    if not row.get(r) or not row[r].strip():
                        raise ValueError(f"Missing mandatory column value: '{r}'")

                code = row["experiment_code"].strip()
                if db.query(Experiment).filter(Experiment.experiment_code == code).first():
                    raise ValueError(f"Duplicate experiment code '{code}' already exists in database")

                lab_code = row["laboratory_code"].strip()
                lab = db.query(Laboratory).filter(Laboratory.code == lab_code).first()
                if not lab:
                    raise ValueError(f"Referenced laboratory code '{lab_code}' not found")

                duration = float(row.get("duration_hours", 2.0))
                if duration <= 0:
                    raise ValueError("Duration hours must be positive")

                students_per_u = int(row.get("students_per_unit", 2))
                min_safe = int(row.get("min_safe_batch", 4))
                max_safe = int(row.get("max_safe_batch", 30))

                exp = Experiment(
                    laboratory_id=lab.id,
                    experiment_code=code,
                    name=row["name"].strip(),
                    description=row.get("description", "").strip(),
                    practical_competency=row["practical_competency"].strip(),
                    duration_hours=duration,
                    students_per_unit=students_per_u,
                    min_safe_batch_size=min_safe,
                    max_safe_batch_size=max_safe,
                    completion_criteria=row.get("completion_criteria", "Practical demonstration and viva.")
                )
                db.add(exp)
                successful_rows += 1

            elif entity_type == "equipment":
                required = ["equipment_code", "name", "laboratory_code", "total_quantity", "functional_quantity"]
                for r in required:
                    if not row.get(r) or not str(row[r]).strip():
                        raise ValueError(f"Missing mandatory column value: '{r}'")

                code = row["equipment_code"].strip()
                if db.query(Equipment).filter(Equipment.equipment_code == code).first():
                    raise ValueError(f"Duplicate equipment code '{code}' already exists")

                lab_code = row["laboratory_code"].strip()
                lab = db.query(Laboratory).filter(Laboratory.code == lab_code).first()
                if not lab:
                    raise ValueError(f"Referenced laboratory code '{lab_code}' not found")

                total = int(row["total_quantity"])
                functional = int(row["functional_quantity"])
                partial = int(row.get("partially_functional_quantity", 0))
                damaged = int(row.get("damaged_quantity", 0))
                maintenance = int(row.get("under_maintenance_quantity", 0))

                if total < 0 or functional < 0 or partial < 0 or damaged < 0 or maintenance < 0:
                    raise ValueError("Equipment quantities cannot be negative numbers")

                if total != (functional + partial + damaged + maintenance):
                    raise ValueError(
                        f"Sum of condition quantities ({functional}+{partial}+{damaged}+{maintenance}={functional+partial+damaged+maintenance}) "
                        f"does not match total_quantity ({total})"
                    )

                eq = Equipment(
                    laboratory_id=lab.id,
                    equipment_code=code,
                    name=row["name"].strip(),
                    total_quantity=total,
                    functional_quantity=functional,
                    partially_functional_quantity=partial,
                    damaged_quantity=damaged,
                    under_maintenance_quantity=maintenance,
                    maintenance_status=row.get("maintenance_status", "Normal").strip()
                )
                db.add(eq)
                successful_rows += 1

            elif entity_type == "students":
                required = ["student_id_number", "name", "email", "batch_code"]
                for r in required:
                    if not row.get(r) or not row[r].strip():
                        raise ValueError(f"Missing mandatory column value: '{r}'")

                sid = row["student_id_number"].strip()
                if db.query(Student).filter(Student.student_id_number == sid).first():
                    raise ValueError(f"Duplicate student ID number '{sid}'")

                email = row["email"].strip()
                if db.query(Student).filter(Student.email == email).first():
                    raise ValueError(f"Student email '{email}' already registered")

                batch_code = row["batch_code"].strip()
                batch = db.query(StudentBatch).filter(StudentBatch.batch_code == batch_code).first()
                if not batch:
                    raise ValueError(f"Referenced batch code '{batch_code}' not found")

                stu = Student(
                    student_id_number=sid,
                    name=row["name"].strip(),
                    email=email,
                    department_id=batch.department_id,
                    batch_id=batch.id
                )
                db.add(stu)
                batch.number_of_students += 1
                successful_rows += 1

            elif entity_type == "batches":
                required = ["batch_code", "batch_name"]
                for r in required:
                    if not row.get(r) or not row[r].strip():
                        raise ValueError(f"Missing mandatory column value: '{r}'")

                bcode = row["batch_code"].strip()
                if db.query(StudentBatch).filter(StudentBatch.batch_code == bcode).first():
                    raise ValueError(f"Duplicate batch code '{bcode}'")

                lab_id = None
                if row.get("laboratory_code"):
                    lab = db.query(Laboratory).filter(Laboratory.code == row["laboratory_code"].strip()).first()
                    if lab:
                        lab_id = lab.id

                batch = StudentBatch(
                    department_id=1,
                    laboratory_id=lab_id,
                    batch_code=bcode,
                    batch_name=row["batch_name"].strip(),
                    number_of_students=int(row.get("number_of_students", 0))
                )
                db.add(batch)
                successful_rows += 1

        except Exception as e:
            rejected_rows += 1
            errors.append(f"Row {idx}: {str(e)}")

    db.commit()

    # Log to import history
    hist = ImportHistory(
        file_name=file.filename or "upload.csv",
        entity_type=entity_type,
        total_rows=total_rows,
        successful_rows=successful_rows,
        rejected_rows=rejected_rows,
        error_log="\n".join(errors) if errors else "None"
    )
    db.add(hist)
    db.commit()

    return {
        "file_name": file.filename,
        "entity_type": entity_type,
        "total_rows": total_rows,
        "successful_rows": successful_rows,
        "rejected_rows": rejected_rows,
        "errors": errors
    }
