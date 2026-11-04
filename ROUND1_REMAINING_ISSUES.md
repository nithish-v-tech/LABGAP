# LABGAP — ROUND 1 REMAINING ISSUES LOG & RESOLUTION MATRIX
**Project:** LABGAP (Practical Learning Coverage and Resource Optimization System)  
**Hackathon Track:** ELITE X | Problem ID: ELX-P25  
**Audit Milestone:** Pre-Round 2 Certification  
**Status:** All Round 1 Critical & Major Audit Issues Resolved

---

## 1. Issue Tracking & Resolution Matrix

| Issue ID | Category | Severity | Description | Resolution Strategy | Automated Verification | Status |
|---|---|---|---|---|---|---|
| **ISSUE-01** | Scheduling Engine | Major | Operating hours violation: Timetable previously included `16:15-18:15`, exceeding 17:00 closing time. | Standardized slots to `09:00-11:00`, `11:15-13:15`, `14:00-16:00`. Enforced runtime check $T_{end} \le close\_time$. | `test_timetable_strictly_within_operating_hours` | **RESOLVED** |
| **ISSUE-02** | Scheduling Engine | Major | Shared equipment over-allocation: Concurrent sessions in different experiments/labs did not check aggregated equipment consumption. | Aggregated committed units across all concurrent sessions for each required equipment. Enforced $\sum committed + needed \le functional\_quantity$. | `test_shared_equipment_concurrency_constraint` | **RESOLVED** |
| **ISSUE-03** | Scheduling Engine | Critical | Missing automatic curriculum allocation for cohorts: Only single-pair generator existed. | Developed `auto_allocate_cohort_curriculum()` with multi-batch rotation and non-conflict calendar filling. Exposed `POST /api/v1/schedule/auto-allocate`. | `test_auto_allocate_cohort_curriculum` | **RESOLVED** |
| **ISSUE-04** | Security / Auth | Critical | Role switcher security clarity: Ensure frontend switcher cannot grant unauthenticated privileges. | Backend derives all permissions from verified HMAC-SHA256 JWT tokens. Switching roles triggers real authentication. Students receive 403 on protected routes. | `test_role_switcher_security_and_permission_enforcement` | **RESOLVED** |
| **ISSUE-05** | Workflow / Repair | Minor | Verification of repair recalibration: Confirming repair must directly restore functional units and improve coverage. | Admin-confirmed repair updates inventory counts, writes audit trail, and capacity recalculation turns NOT COVERED to FULLY COVERED. | `test_repair_workflow_and_coverage_recalibration` | **RESOLVED** |
| **ISSUE-06** | Testing | Major | Starlette `TestClient` hang on Windows: Synchronous anyio blocking portal caused test runner deadlocks. | Implemented pure synchronous test architecture testing endpoints with session context directly. 21 tests execute in 7.69s. | `test_api_endpoints.py` (21 tests) | **RESOLVED** |

---

## 2. Non-Blocking Considerations for Round 2

1. **Multi-Institution Tenancy Expansion:**
   - *Current State:* Institution and Department models exist with complete foreign keys; single-department demo is fully populated.
   - *Round 2 Scope:* Support cross-departmental sharing agreements and multi-campus equipment transfers.

2. **Automated Preventive Maintenance Scheduling:**
   - *Current State:* Equipment tracks maintenance status (`Normal`, `Scheduled`, `Overdue`) and damaged quantities.
   - *Round 2 Scope:* Implement predictive maintenance alerts based on hours of operation and student session counts.

3. **Advanced IoT / QR-Code Physical Check-in:**
   - *Current State:* Faculty explicitly marks and verifies attendance and viva marks via the verification dashboard.
   - *Round 2 Scope:* Integrate QR badge generation for instantaneous student bench check-ins.
