# LABGAP: Practical Learning Coverage and Resource Optimization System
**Hackathon:** ELITE X | **Problem ID:** ELX-P25 | **Track:** 5 — Civic Engagement & Campus Community  
**Tagline:** *Bridging Practical Learning Gaps Through Intelligent Resource Optimization*

---

## 🚀 Live Working Prototype URLs

- **Frontend Application:** [http://127.0.0.1:5173/](http://127.0.0.1:5173/)
- **Backend Core API:** [http://127.0.0.1:8000/](http://127.0.0.1:8000/)
- **Interactive Swagger Documentation:** [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
- **API Health Check:** [http://127.0.0.1:8000/health](http://127.0.0.1:8000/health)

---

## 👥 4 User Role Demo Accounts (1-Click Fast Login Available)

| Role | Email | Password | Primary Permissions & Responsibilities |
|---|---|---|---|
| **Laboratory Administrator** | `admin@labgap.demo` | `AdminPassword123!` | Full control: Manage labs, experiments, equipment, CSV import, schedule generation, repair confirmation. |
| **Faculty / Lab Instructor** | `faculty@labgap.demo` | `FacultyPassword123!` | View assigned cohorts & practicals, record participation, verify completion (**Pending → Verified/Rejected**). |
| **Student** | `student@labgap.demo` | `StudentPassword123!` | View personal laboratory schedule, pending practicals, verified competencies (**Strictly read-only**). |
| **Head of Department (HOD)** | `hod@labgap.demo` | `HodPassword123!` | Department-level coverage summary, learning gap audits, equipment health, repair oversight (**Read-only**). |

> 💡 **Hackathon Feature:** A quick **One-Click Role Switcher** is present in the top navigation bar of the application, allowing instant persona switching without manually signing out and in!

---

## ⚙️ Core Engineering Architecture & Algorithmic Decisions

### 1. Deterministic Capacity & Coverage Engine (`backend/app/algorithms/capacity_engine.py`)
- **Functional Equipment Availability:** Only certified working units (`functional_quantity`) are counted. Damaged and under-maintenance units are strictly excluded.
- **Session Capacity:**  
  $$\text{Capacity per Session} = \min(\text{Active Stations} \times \text{Students per Unit},\; \text{Max Safe Batch Size})$$
- **Coverage Classification:**
  - **`FULLY COVERED`**: All assigned students can be accommodated within safe equipment capacity and timetable hours.
  - **`PARTIALLY COVERED`**: Equipment shortage or time constraints prevent the complete batch from completing practicals in the allotted weekly hours.
  - **`NOT COVERED`**: Zero functional units of critical equipment or capacity below minimum safe batch size.

### 2. Practical Learning Gap Calculator (`backend/app/algorithms/gap_analyzer.py`)
- **Strict Institutional Rule:** **Attendance alone is NOT proof of practical competence.**
- Only records where `participation_status == 'Completed'` **AND** `verification_status == 'Verified'` count towards verified coverage:
  $$\text{Verified Coverage \%} = \left(\frac{\text{Faculty-Verified Completions}}{\text{Total Assigned Students}}\right) \times 100$$
  $$\text{Learning Gap} = \text{Total Assigned Students} - \text{Verified Completions}$$

### 3. Constraint-Based Scheduling Engine (`backend/app/algorithms/scheduling_engine.py`)
- Generates non-conflicting student rotation sessions.
- **Constraints Enforced:** No laboratory double-booking, no faculty scheduling overlap, safe batch limits, and laboratory operating hours (09:00 - 17:00).
- Prioritizes students who still lack verified practical completion.

### 4. ROI-Driven Equipment Repair Prioritizer (`backend/app/algorithms/repair_engine.py`)
- Evaluates damaged inventory and ranks repair candidates into **Critical**, **High**, **Medium**, and **Low** based on:
  - Number of blocked syllabus experiments.
  - Number of students impacted.
  - Potential capacity gain (additional safe student seats restored).
- **Enforcement:** Equipment is never automatically marked functional. Administrator must explicitly inspect and confirm physical repairs.

---

## 📊 Benchmark Synthetic Dataset

The system includes a realistic demonstration dataset for **Apex Institute of Technology & Engineering (EEE Department)**:
- **4 Laboratories:** Analog & Digital Electronics, Embedded Systems, Power Systems & Machines, RF Communications.
- **15 Practical Experiments:** Spanning all three coverage classifications (`FULLY COVERED`, `PARTIALLY COVERED`, `NOT COVERED`).
- **20 Equipment Types:** With complete condition breakdowns ($\text{Total} = \text{Functional} + \text{Partial} + \text{Damaged} + \text{Maintenance}$).
- **68 Synthetic Students:** Across 3 distinct cohorts (Batch A, Batch B, Batch C).
- **Realistic Verified History:** Illustrating verified competencies, pending reviews, partial completions, and unverified gaps.

---

## 🛠️ Launch & Development Commands

### PowerShell Terminal 1: Backend API
```powershell
cd C:\Users\MAHARAJ\Downloads\LABGAP\backend
python -m uvicorn main:app --reload --host 127.0.0.1 --port 8000
```

### PowerShell Terminal 2: React Frontend
```powershell
cd C:\Users\MAHARAJ\Downloads\LABGAP\frontend
npm run dev -- --host 127.0.0.1 --port 5173
```

---

## 🧪 Automated Testing Verification

Automated Pytest test suites verify:
- Functional equipment exclusion rules.
- Deterministic capacity and coverage formulas.
- Attendance vs. Verified Competence differentiation.
- Student self-approval prevention (403 Forbidden).
- HOD read-only enforcement (403 Forbidden).
- Sum-of-condition inventory consistency checks.

To execute the test suite:
```powershell
cd C:\Users\MAHARAJ\Downloads\LABGAP\backend
python -m pytest tests/test_algorithms.py tests/test_api_auth.py tests/test_csv_validation.py tests/test_verification.py -v
```
*(Result: **11 passed, 0 failed**)*
