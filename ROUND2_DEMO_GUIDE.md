# LABGAP — ROUND 2 DEMONSTRATION GUIDE
**Project Title:** LABGAP (Practical Learning Coverage and Resource Optimization System)  
**Hackathon:** ELITE X | **Problem ID:** ELX-P25 | **Track:** 5 — Civic Engagement & Campus Community  
**Version:** Round 2 Working Prototype  

---

## 1. System Launch Instructions

### Terminal 1: Backend API (FastAPI)
```powershell
cd c:\Users\MAHARAJ\Downloads\LABGAP\backend
uvicorn app.main:app --host 0.0.0.0 --port 8000
```
- **Backend API URL:** `http://localhost:8000`
- **Interactive Swagger Documentation:** `http://localhost:8000/docs`

### Terminal 2: Frontend Web Client (React + Vite)
```powershell
cd c:\Users\MAHARAJ\Downloads\LABGAP\frontend
npm run dev
```
- **Web Application URL:** `http://localhost:5173`

---

## 2. Pre-Configured Demo Credentials

| Role | Email | Password | Primary Portal Capabilities |
|---|---|---|---|
| **Administrator** | `admin@labgap.demo` | `AdminPassword123!` | Smart Lab Allocation, Inventory, Curricula, Resource Intelligence, Timetabling |
| **Faculty Instructor** | `faculty@labgap.demo` | `FacultyPassword123!` | Practical Viva Verification, Student Competencies, Lab Attendance |
| **Student** | `student@labgap.demo` | `StudentPassword123!` | My Competencies, Personal Learning Gaps, Assigned Practicals, Timetable |
| **Head of Dept (HOD)** | `hod@labgap.demo` | `HodPassword123!` | Departmental Analytics, Resource Utilization, Accreditation Summaries |

---

## 3. Step-by-Step 5-Minute Evaluator Demo Walkthrough

### Step 1: Login & Role Selection
1. Open `http://localhost:5173`.
2. Click the quick-fill button **"Admin"** on the login screen (or enter `admin@labgap.demo` / `AdminPassword123!`).
3. Click **"Sign In to LABGAP"**.
4. Observe the Overview dashboard displaying real institutional metrics for **Apex Institute of Technology** (4 Laboratories, 15 Experiments, 20 Equipment Categories, 68 Students).

### Step 2: Feature One — Smart Lab Allocation
1. From the sidebar navigation, click **"Smart Lab Allocation"**.
2. Select **Target Student Cohort:** `BATCH-2026-A (24 Students) — Power & Electronics Core`.
3. Select **Target Experiment:** `EXP-01 — Transistor Characteristics (BJT/MOSFET)`.
4. Click **"Find Best Laboratory"**.
5. Observe the Rule-Based Evaluation:
   - **Rank #1 Recommendation:** `Electronics & Circuits Laboratory` with a Suitability Score of **94.8/100**.
   - Notice the breakdown: 10 active stations (20 capacity/session), room capacity compliant, low contention.
   - Observe the **Ineligible / Disqualified Facilities** section: laboratories lacking required functional oscilloscopes are scored **0/100 (Infeasible)** with clear explanations.
6. Click **"Approve Allocation"**:
   - The system validates feasibility, assigns the experiment, generates rotation sessions into the database calendar, and displays a green success confirmation banner.

### Step 3: Feature Two — Student Practical Competency Tracking
1. From the sidebar, click **"Student Competencies"**.
2. Observe the cohort KPI summary:
   - Average Verified Competency Rate.
   - Fully Competent Students vs Students with Practical Learning Gaps.
3. Review the student progress cards:
   - Notice the color-coded visual progress bars (Green = Proficient, Amber = Progressing, Red = At Risk).
4. Click on any student row (e.g., `Aarav Sharma`) to expand the **Curriculum Practicals Verification Breakdown**:
   - Displays each experiment, participation status, faculty verification status, and instructor viva notes.
   - Confirms that *attendance does not equal competence*: unverified practicals remain as learning gaps.

### Step 4: Feature Three — Resource Intelligence & Decision Engine
1. From the sidebar, click **"Resource Intelligence"**.
2. Review the Hardware & Coverage Pulse cards (Equipment Utilization, Broken Equipment, Curriculum Blockers).
3. Review the **Prioritized Operational Recommendations**:
   - **Equipment Repair Impact:** Points out how repairing specific damaged equipment restores $+12$ student capacity and unblocks experiments.
   - **Capacity Utilization:** Identifies laboratories with $>60\%$ unallocated slot capacity ready for additional cohort practicals.
   - **Curriculum Feasibility Alerts:** Identifies experiments classified as `NOT COVERED` due to bottleneck equipment shortages.

### Step 5: Feature Four — Schedule Optimization & Operating Hours
1. From the sidebar, click **"Schedule Optimization"**.
2. Observe the scheduled rotation calendar:
   - All session times are strictly within institutional hours (`09:00–11:00`, `11:15–13:15`, or `14:00–16:00`).
   - Zero sessions end past `17:00`.
   - Zero duplicate laboratory bookings, faculty collisions, or cohort overlaps.

### Step 6: Faculty Practical Verification Workflow
1. Use the top navbar role switcher to switch to **"Faculty"** (or log in as `faculty@labgap.demo`).
2. Navigate to **"Practical Verification"**.
3. Select an experiment and student batch.
4. Record student viva assessment notes and click **"Verify Competency"**.
5. Switch back to **"Student Competencies"** or **"Student Portal"** to verify that the student's learning gap is closed immediately in real time.

---

## 4. Key Security & Verification Invariants Proven

1. **Student Self-Verification Blocked:** Student role attempting to call verification or allocation endpoints receives HTTP 403 Forbidden.
2. **Infeasible Allocation Blocked:** Approving an allocation to a laboratory with 0 functional units of mandatory equipment returns HTTP 400 Bad Request with explicit bottleneck reasons.
3. **Shared Equipment Guard:** Concurrent practical sessions requiring the same apparatus across different rooms cannot exceed available functional inventory.
4. **All 24 automated tests passing** in `backend/tests/`.
