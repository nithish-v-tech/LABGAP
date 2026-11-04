import datetime
from app.database.connection import SessionLocal, Base, engine
from app.database.models import (
    Institution, Department, Role, User, Laboratory, Faculty,
    StudentBatch, Student, Equipment, Experiment, ExperimentEquipment,
    BatchExperiment, CompletionRecord, Schedule, RepairRecord
)
from app.security.auth import hash_password

def seed_database():
    db = SessionLocal()
    try:
        # Drop all tables and recreate to guarantee fresh seed
        Base.metadata.drop_all(bind=engine)
        Base.metadata.create_all(bind=engine)

        print("[Seed] Creating Institution and Department...")
        inst = Institution(
            name="Apex Institute of Technology & Engineering",
            code="AITE-CAMPUS",
            address="Innovation Corridor, Tech City"
        )
        db.add(inst)
        db.flush()

        dept = Department(
            institution_id=inst.id,
            name="Department of Electrical & Electronics Engineering",
            code="EEE-DEPT"
        )
        db.add(dept)
        db.flush()

        print("[Seed] Creating Roles...")
        roles_data = [
            ("admin", "Laboratory Administrator - Full technical and operational access"),
            ("faculty", "Faculty / Lab Instructor - Verification and student assessment"),
            ("student", "Student - Personal laboratory schedule and competency view"),
            ("hod", "Head of Department - Read-only department analytics & repair oversight")
        ]
        role_objs = {}
        for rname, rdesc in roles_data:
            role = Role(name=rname, description=rdesc)
            db.add(role)
            db.flush()
            role_objs[rname] = role

        print("[Seed] Creating Demonstration User Accounts...")
        users_seed = [
            ("admin@labgap.demo", "AdminPassword123!", "Suresh Narayanan (Lab Admin)", "admin"),
            ("faculty@labgap.demo", "FacultyPassword123!", "Dr. Rajesh Ramanathan (Professor)", "faculty"),
            ("student@labgap.demo", "StudentPassword123!", "Aarav Patel (Student)", "student"),
            ("hod@labgap.demo", "HodPassword123!", "Dr. Meenakshi Iyer (HOD)", "hod"),
            ("faculty2@labgap.demo", "FacultyPassword123!", "Prof. Sneha Kulkarni", "faculty"),
            ("faculty3@labgap.demo", "FacultyPassword123!", "Prof. Vikram Sen", "faculty")
        ]
        user_objs = {}
        for email, pwd, fname, rname in users_seed:
            u = User(
                email=email,
                hashed_password=hash_password(pwd),
                full_name=fname,
                role_id=role_objs[rname].id,
                department_id=dept.id,
                is_active=True
            )
            db.add(u)
            db.flush()
            user_objs[email] = u

        print("[Seed] Creating Laboratories...")
        labs_data = [
            ("LAB-EC-01", "Analog & Digital Electronics Laboratory", "Block B, Room 204", 30, "09:00", "17:00"),
            ("LAB-MC-01", "Microcontrollers & Embedded Systems Laboratory", "Block C, Room 102", 28, "09:00", "17:00"),
            ("LAB-PS-01", "Electrical Power Systems & Machines Laboratory", "Heavy Machinery Wing, Room 001", 24, "09:00", "17:00"),
            ("LAB-RF-01", "RF & Advanced Communications Laboratory", "Research Block, Room 305", 20, "09:00", "17:00")
        ]
        lab_objs = {}
        for code, name, loc, cap, op, cl in labs_data:
            lab = Laboratory(
                department_id=dept.id,
                code=code,
                name=name,
                location=loc,
                max_student_capacity=cap,
                working_days="Monday to Friday",
                open_time=op,
                close_time=cl
            )
            db.add(lab)
            db.flush()
            lab_objs[code] = lab

        print("[Seed] Creating Faculty Profiles...")
        fac1 = Faculty(
            user_id=user_objs["faculty@labgap.demo"].id,
            department_id=dept.id,
            faculty_code="FAC-EEE-01",
            name="Dr. Rajesh Ramanathan",
            email="faculty@labgap.demo",
            assigned_laboratory_id=lab_objs["LAB-EC-01"].id
        )
        db.add(fac1)
        db.flush()
        lab_objs["LAB-EC-01"].assigned_faculty_id = fac1.id

        fac2 = Faculty(
            user_id=user_objs["faculty2@labgap.demo"].id,
            department_id=dept.id,
            faculty_code="FAC-EEE-02",
            name="Prof. Sneha Kulkarni",
            email="faculty2@labgap.demo",
            assigned_laboratory_id=lab_objs["LAB-MC-01"].id
        )
        db.add(fac2)
        db.flush()
        lab_objs["LAB-MC-01"].assigned_faculty_id = fac2.id

        fac3 = Faculty(
            user_id=user_objs["faculty3@labgap.demo"].id,
            department_id=dept.id,
            faculty_code="FAC-EEE-03",
            name="Prof. Vikram Sen",
            email="faculty3@labgap.demo",
            assigned_laboratory_id=lab_objs["LAB-PS-01"].id
        )
        db.add(fac3)
        db.flush()
        lab_objs["LAB-PS-01"].assigned_faculty_id = fac3.id

        print("[Seed] Creating Student Batches...")
        batches_data = [
            ("BATCH-2026-A", "3rd Year EEE - Section A", lab_objs["LAB-EC-01"].id, 24, fac1.id),
            ("BATCH-2026-B", "3rd Year EEE - Section B", lab_objs["LAB-MC-01"].id, 24, fac2.id),
            ("BATCH-2026-C", "2nd Year EEE - Core Electrical", lab_objs["LAB-PS-01"].id, 20, fac3.id)
        ]
        batch_objs = {}
        for bcode, bname, lid, num, fid in batches_data:
            b = StudentBatch(
                department_id=dept.id,
                laboratory_id=lid,
                batch_code=bcode,
                batch_name=bname,
                number_of_students=num,
                assigned_faculty_id=fid
            )
            db.add(b)
            db.flush()
            batch_objs[bcode] = b

        print("[Seed] Creating 68 Synthetic Students...")
        indian_names = [
            "Aarav Patel", "Diya Sharma", "Aditya Nair", "Ananya Reddy", "Rohan Deshmukh",
            "Kavya Sundaram", "Varun Iyer", "Pooja Verma", "Siddharth Joshi", "Meera Pillai",
            "Nikhil Menon", "Tanvi Bhat", "Arjun Kulkarni", "Isha Mukherjee", "Rishi Kapoor",
            "Shreya Sen", "Akash Gupta", "Rhea Sengupta", "Karan Malhotra", "Divya Chauhan",
            "Manish Pandey", "Sneha Roy", "Pranav Rao", "Neha Saxena",
            # Batch B
            "Rahul Varma", "Anika Das", "Gaurav Mehta", "Priyanka Nambiar", "Devendra Singh",
            "Bhavna Aggarwal", "Kunal Chopra", "Swati Hegde", "Vivek Anand", "Lavanya Krishnan",
            "Harsh Vardhan", "Nandini Rathi", "Ayush Agrawal", "Ritika Prasad", "Sanjay Namboodiri",
            "Tarun Chawla", "Deepika Shenoy", "Sameer Bhatt", "Pallavi Dixit", "Abhishek Tiwari",
            "Ritu Singhal", "Kartik Pillai", "Smriti Mishra", "Alok Sengupta",
            # Batch C
            "Gautam Bajaj", "Madhuri Gowda", "Chirag Sethi", "Kiran Balakrishnan", "Tejas Prabhu",
            "Shruti Mittal", "Naveen Kaushik", "Ankita Dutta", "Saurabh Jha", "Payal Jain",
            "Mayank Mathur", "Geeta Bhattacharya", "Bhavesh Lad", "Urvashi Somani", "Yash Saraf",
            "Hemant Parekh", "Mugdha Dani", "Chetan Shirke", "Sunita Rathod", "Omkar Bhave"
        ]

        student_objs = []
        for i, name in enumerate(indian_names, start=1):
            sid_num = f"2026-EEE-{i:03d}"
            # Split into batches: 1-24 -> Batch A, 25-48 -> Batch B, 49-68 -> Batch C
            if i <= 24:
                b_assign = batch_objs["BATCH-2026-A"]
            elif i <= 48:
                b_assign = batch_objs["BATCH-2026-B"]
            else:
                b_assign = batch_objs["BATCH-2026-C"]

            # If i == 1, attach user_objs["student@labgap.demo"]
            assigned_user_id = user_objs["student@labgap.demo"].id if i == 1 else None

            stu = Student(
                user_id=assigned_user_id,
                student_id_number=sid_num,
                name=name,
                email=f"{name.lower().replace(' ', '.')}@student.labgap.demo" if i != 1 else "student@labgap.demo",
                department_id=dept.id,
                batch_id=b_assign.id
            )
            db.add(stu)
            db.flush()
            student_objs.append(stu)

        print("[Seed] Creating 20 Equipment Types with Condition Breakdown...")
        # (code, name, lab_code, total, func, partial, damaged, maint, maint_status, repair_status)
        eq_data = [
            ("EQ-01", "Digital Storage Oscilloscope 100MHz", "LAB-EC-01", 12, 9, 1, 2, 0, "Normal", "Inspection Required"),
            ("EQ-02", "Function / Arbitrary Waveform Generator", "LAB-EC-01", 10, 8, 0, 2, 0, "Normal", "Inspection Required"),
            ("EQ-03", "Triple Output Regulated DC Power Supply", "LAB-EC-01", 14, 12, 1, 1, 0, "Normal", "In Repair"),
            ("EQ-04", "Digital Multimeter 4.5 Digit True RMS", "LAB-EC-01", 20, 18, 0, 2, 0, "Normal", "None"),
            ("EQ-05", "Breadboard Station with Built-in Analog Meter", "LAB-EC-01", 16, 14, 2, 0, 0, "Normal", "None"),
            ("EQ-06", "ARM Cortex-M4 STM32 Development Board", "LAB-MC-01", 15, 13, 0, 1, 1, "Scheduled", "In Repair"),
            ("EQ-07", "In-Circuit ST-Link V2 Debugger", "LAB-MC-01", 15, 12, 0, 3, 0, "Normal", "Inspection Required"),
            ("EQ-08", "Logic Analyzer 16-Channel USB", "LAB-MC-01", 8, 6, 0, 2, 0, "Normal", "Inspection Required"),
            ("EQ-09", "I2C/SPI Sensor Interfacing Evaluation Board", "LAB-MC-01", 12, 10, 1, 1, 0, "Normal", "None"),
            ("EQ-10", "8051 Microcontroller Trainer Kit", "LAB-MC-01", 10, 7, 1, 2, 0, "Overdue", "Inspection Required"),
            # Power Systems Lab (Heavy equipment)
            ("EQ-11", "Three-Phase Squirrel Cage Induction Motor 3HP", "LAB-PS-01", 4, 1, 0, 2, 1, "Overdue", "Inspection Required"), # CRITICAL BOTTLENECK!
            ("EQ-12", "DC Shunt Motor-Generator Coupled Set", "LAB-PS-01", 4, 2, 0, 1, 1, "Scheduled", "In Repair"),
            ("EQ-13", "3-Phase Auto-Transformer (Variac) 15A", "LAB-PS-01", 5, 3, 0, 1, 1, "Normal", "In Repair"),
            ("EQ-14", "Resistive / Inductive 3-Phase Load Bank", "LAB-PS-01", 4, 2, 0, 2, 0, "Normal", "Inspection Required"),
            ("EQ-15", "Digital Power Analyzer / Wattmeter", "LAB-PS-01", 6, 4, 0, 1, 1, "Normal", "Inspection Required"),
            ("EQ-16", "Precision LCR Bridge Meter", "LAB-EC-01", 4, 3, 1, 0, 0, "Normal", "None"),
            # RF Lab (High-tech)
            ("EQ-17", "Spectrum Analyzer 1.5GHz", "LAB-RF-01", 2, 0, 0, 1, 1, "Overdue", "Inspection Required"), # 0 FUNCTIONAL!
            ("EQ-18", "High Voltage Insulation Tester (Megger)", "LAB-PS-01", 4, 3, 0, 1, 0, "Normal", "None"),
            ("EQ-19", "Digital Tachometer Optical/Contact", "LAB-PS-01", 6, 5, 0, 1, 0, "Normal", "None"),
            ("EQ-20", "SMD Soldering & Desoldering Station", "LAB-EC-01", 8, 6, 1, 1, 0, "Normal", "None")
        ]
        eq_objs = {}
        for code, name, lcode, tot, fnc, prt, dmg, mnt, mstat, rstat in eq_data:
            # Validate condition sums
            assert tot == (fnc + prt + dmg + mnt), f"Invalid seed equipment count for {code}"
            eq = Equipment(
                laboratory_id=lab_objs[lcode].id,
                equipment_code=code,
                name=name,
                description=f"Standard laboratory-grade {name} for undergraduate engineering.",
                total_quantity=tot,
                functional_quantity=fnc,
                partially_functional_quantity=prt,
                damaged_quantity=dmg,
                under_maintenance_quantity=mnt,
                maintenance_status=mstat,
                repair_status=rstat
            )
            db.add(eq)
            db.flush()
            eq_objs[code] = eq

        print("[Seed] Creating 15 Practical Experiments...")
        # (code, name, lab_code, competency, duration, students_per_unit, min_batch, max_batch, req_eq_code, qty_req)
        exp_data = [
            # Analog & Digital Electronics Lab (LAB-EC-01)
            ("EXP-EC-01", "Inverting and Non-Inverting Op-Amp Amplifiers", "LAB-EC-01", "Analog Circuit Synthesis", 2.0, 2, 4, 24, "EQ-01", 1),
            ("EXP-EC-02", "RC Phase Shift and Wien Bridge Oscillators", "LAB-EC-01", "Frequency Response Analysis", 2.0, 2, 4, 24, "EQ-02", 1),
            ("EXP-EC-03", "Precision Full-Wave Rectifier with Voltage Regulators", "LAB-EC-01", "Power Electronics Fundamentals", 2.0, 2, 4, 24, "EQ-03", 1),
            ("EXP-EC-04", "Digital Multimeter Calibration & Tolerance Testing", "LAB-EC-01", "Instrumentation Metrology", 1.5, 2, 4, 30, "EQ-04", 1),
            ("EXP-EC-05", "SMD Soldering and PCB Prototype Assembly", "LAB-EC-01", "Hardware Fabrication & Testing", 2.5, 2, 4, 20, "EQ-20", 1),

            # Microcontrollers & Embedded Systems Lab (LAB-MC-01)
            ("EXP-MC-01", "ARM Cortex-M4 GPIO Interfacing and Interrupt Handling", "LAB-MC-01", "Embedded C Firmware Design", 2.0, 2, 4, 26, "EQ-06", 1),
            ("EXP-MC-02", "In-Circuit Debugging & Memory Dump Analysis with ST-Link", "LAB-MC-01", "Firmware Debugging & Verification", 2.0, 2, 4, 24, "EQ-07", 1),
            ("EXP-MC-03", "I2C/SPI Sensor Bus Protocol Decoding with Logic Analyzer", "LAB-MC-01", "Digital Communication Protocols", 2.5, 2, 4, 20, "EQ-08", 1),
            ("EXP-MC-04", "Multi-Sensor Environmental Telemetry Interfacing", "LAB-MC-01", "IoT Sensor Integration", 2.0, 2, 4, 24, "EQ-09", 1),
            ("EXP-MC-05", "8051 Timer Interrupts and Stepper Motor Controller", "LAB-MC-01", "Legacy Microcontroller Interfacing", 2.0, 2, 4, 20, "EQ-10", 1),

            # Electrical Power Systems & Machines Lab (LAB-PS-01)
            ("EXP-PS-01", "Three-Phase Induction Motor Circle Diagram & Load Test", "LAB-PS-01", "AC Machine Parameter Calculation", 3.0, 3, 6, 24, "EQ-11", 1), # NOT COVERED (EQ-11 has only 1 func)
            ("EXP-PS-02", "DC Shunt Motor Ward-Leonard Speed Control", "LAB-PS-01", "DC Motor Speed Regulation", 3.0, 3, 6, 20, "EQ-12", 1), # PARTIALLY COVERED (EQ-12 has 2 func)
            ("EXP-PS-03", "Three-Phase Transformer Open/Short Circuit Test", "LAB-PS-01", "Transformer Efficiency Analysis", 2.5, 3, 6, 24, "EQ-13", 1), # PARTIALLY COVERED
            ("EXP-PS-04", "Active and Reactive Power Measurement using Wattmeter", "LAB-PS-01", "Power System Harmonic Analysis", 2.0, 2, 4, 24, "EQ-15", 1),

            # RF Lab (LAB-RF-01)
            ("EXP-RF-01", "RF Harmonic Distortion and Spectrum Analysis", "LAB-RF-01", "RF Signal Metrology", 3.0, 2, 4, 16, "EQ-17", 1) # NOT COVERED (EQ-17 has 0 func)
        ]

        exp_objs = {}
        for code, name, lcode, comp, dur, spu, minb, maxb, eqcode, qreq in exp_data:
            exp = Experiment(
                laboratory_id=lab_objs[lcode].id,
                experiment_code=code,
                name=name,
                description=f"Prescribed curriculum experiment for {comp}.",
                practical_competency=comp,
                duration_hours=dur,
                students_per_unit=spu,
                min_safe_batch_size=minb,
                max_safe_batch_size=maxb,
                completion_criteria="Circuit assembly, waveform capture, calibrated readings and faculty viva examination."
            )
            db.add(exp)
            db.flush()
            exp_objs[code] = exp

            # Link required equipment
            link = ExperimentEquipment(
                experiment_id=exp.id,
                equipment_id=eq_objs[eqcode].id,
                quantity_required=qreq,
                is_critical=True
            )
            db.add(link)

        print("[Seed] Assigning Experiments to Batches...")
        # Batch A gets Analog Electronics experiments
        for exp_code in ["EXP-EC-01", "EXP-EC-02", "EXP-EC-03", "EXP-EC-04", "EXP-EC-05"]:
            db.add(BatchExperiment(batch_id=batch_objs["BATCH-2026-A"].id, experiment_id=exp_objs[exp_code].id))

        # Batch B gets Microcontroller experiments
        for exp_code in ["EXP-MC-01", "EXP-MC-02", "EXP-MC-03", "EXP-MC-04", "EXP-MC-05"]:
            db.add(BatchExperiment(batch_id=batch_objs["BATCH-2026-B"].id, experiment_id=exp_objs[exp_code].id))

        # Batch C gets Power Systems experiments
        for exp_code in ["EXP-PS-01", "EXP-PS-02", "EXP-PS-03", "EXP-PS-04", "EXP-RF-01"]:
            db.add(BatchExperiment(batch_id=batch_objs["BATCH-2026-C"].id, experiment_id=exp_objs[exp_code].id))

        db.flush()

        print("[Seed] Creating Realistic Practical Completion & Verification Records...")
        # For EXP-EC-01 (Inverting Op-Amp), students 1 to 16 have Verified completed
        for stu in student_objs[:16]:
            db.add(CompletionRecord(
                student_id=stu.id,
                experiment_id=exp_objs["EXP-EC-01"].id,
                batch_id=batch_objs["BATCH-2026-A"].id,
                participation_status="Completed",
                verification_status="Verified",
                instructor_id=fac1.id,
                verification_timestamp=datetime.datetime.utcnow() - datetime.timedelta(days=2),
                assessment_notes="Excellent gain curve calibration. Viva cleared with distinction."
            ))

        # Students 17 to 20 have Participated but Pending verification
        for stu in student_objs[16:20]:
            db.add(CompletionRecord(
                student_id=stu.id,
                experiment_id=exp_objs["EXP-EC-01"].id,
                batch_id=batch_objs["BATCH-2026-A"].id,
                participation_status="Completed",
                verification_status="Pending",
                instructor_id=fac1.id,
                assessment_notes="Oscilloscope waveform recorded. Pending final viva evaluation."
            ))

        # Students 21 to 24 have Partially completed (e.g. circuit built but not calibrated)
        for stu in student_objs[20:24]:
            db.add(CompletionRecord(
                student_id=stu.id,
                experiment_id=exp_objs["EXP-EC-01"].id,
                batch_id=batch_objs["BATCH-2026-A"].id,
                participation_status="Partially completed",
                verification_status="Pending",
                instructor_id=fac1.id,
                assessment_notes="Circuit built; offset voltage trimmer not calibrated before lab session timed out."
            ))

        # For EXP-MC-01, students 25 to 36 have Verified completed
        for stu in student_objs[24:36]:
            db.add(CompletionRecord(
                student_id=stu.id,
                experiment_id=exp_objs["EXP-MC-01"].id,
                batch_id=batch_objs["BATCH-2026-B"].id,
                participation_status="Completed",
                verification_status="Verified",
                instructor_id=fac2.id,
                verification_timestamp=datetime.datetime.utcnow() - datetime.timedelta(days=1),
                assessment_notes="STM32 GPIO timer interrupt code compiled and verified on hardware."
            ))

        # For EXP-PS-01 (Induction Motor), zero verified completions because equipment is damaged!

        print("[Seed] Generating Initial Feasible Schedules...")
        # Create a few upcoming rotation sessions for Batch A and Batch B
        tomorrow = (datetime.date.today() + datetime.timedelta(days=1)).strftime("%Y-%m-%d")
        day_after = (datetime.date.today() + datetime.timedelta(days=2)).strftime("%Y-%m-%d")

        db.add(Schedule(
            experiment_id=exp_objs["EXP-EC-02"].id,
            batch_id=batch_objs["BATCH-2026-A"].id,
            laboratory_id=lab_objs["LAB-EC-01"].id,
            faculty_id=fac1.id,
            session_number=1,
            date=tomorrow,
            start_time="09:00",
            end_time="11:00",
            student_capacity=16,
            expected_students=12,
            remaining_learning_gap=12,
            status="Scheduled"
        ))

        db.add(Schedule(
            experiment_id=exp_objs["EXP-MC-02"].id,
            batch_id=batch_objs["BATCH-2026-B"].id,
            laboratory_id=lab_objs["LAB-MC-01"].id,
            faculty_id=fac2.id,
            session_number=1,
            date=day_after,
            start_time="11:15",
            end_time="13:15",
            student_capacity=14,
            expected_students=14,
            remaining_learning_gap=10,
            status="Scheduled"
        ))

        db.commit()
        print("[Seed] Database seed completed successfully!")
        return True

    except Exception as e:
        db.rollback()
        print(f"[Seed] Error during seeding: {e}")
        raise e
    finally:
        db.close()

if __name__ == "__main__":
    seed_database()
