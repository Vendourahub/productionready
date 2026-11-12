# ProductionReady — Setup, Configuration & Architecture Guide

This document details the database schema, environment configuration, working API endpoints, and end-to-end execution workflow for **ProductionReady Phase 2**.

---

## 1. System Architecture

```
                                  +-----------------------------+
                                  |   Connected Codebase Intake |
                                  | (Local Path or GitHub Repo) |
                                  +--------------+--------------+
                                                 |
                                                 v
                                  +-----------------------------+
                                  | Ephemeral Sandbox Workspace |
                                  | (Zero Code Retention/Tempfs)|
                                  +--------------+--------------+
                                                 |
                   +-----------------------------+-----------------------------+
                   |                             |                             |
                   v                             v                             v
       +-----------------------+     +-----------------------+     +-----------------------+
       | Custom Scanner Rules  |     |   Supabase RLS & SQL  |     | Webhook & Secret Leak |
       | (Secrets, Keys, CORS) |     |  (Access Control AST) |     |  (Client Environment) |
       +-----------+-----------+     +-----------+-----------+     +-----------+-----------+
                   |                             |                             |
                   +-----------------------------+-----------------------------+
                                                 |
                                                 v
                                  +-----------------------------+
                                  |   Evidence & Ledger Engine  |
                                  | (Pass vs Defect vs Gap ASVS)|
                                  +--------------+--------------+
                                                 |
                   +-----------------------------+-----------------------------+
                   |                                                           |
                   v                                                           v
       +-----------------------+                                   +-----------------------+
       |   PostgreSQL / SQLite |                                   | Next.js Web Dashboard |
       |   Persistence Layer   |                                   |  (Projects, Audits,   |
       |  (5 Relational Tables)|                                   |      Remediation)     |
       +-----------------------+                                   +-----------------------+
```

---

## 2. Database Schema & Tables

ProductionReady uses **SQLAlchemy 2.0 ORM** compatible with both **PostgreSQL** (production) and **SQLite** (local development & testing).

### Table: `projects`
Stores registered repositories and branch tracking configuration.
| Column | Type | Constraints | Description |
| :--- | :--- | :--- | :--- |
| `id` | `VARCHAR(36)` | `PRIMARY KEY` | UUIDv4 identifier |
| `name` | `VARCHAR(255)` | `NOT NULL` | Project name displayed on dashboard |
| `repository_url` | `VARCHAR(512)` | `NOT NULL` | Git clone URL or local directory path |
| `default_branch` | `VARCHAR(100)` | `DEFAULT 'main'` | Target branch for automated scans |
| `created_at` | `DATETIME` | `DEFAULT UTC` | Registration timestamp |
| `updated_at` | `DATETIME` | `DEFAULT UTC` | Last modification timestamp |

*Relationships:* `assessments` (1-to-many, `cascade="all, delete-orphan"`).

---

### Table: `assessments`
Records individual verification runs, readiness verdicts, and auditor sign-offs.
| Column | Type | Constraints | Description |
| :--- | :--- | :--- | :--- |
| `id` | `VARCHAR(36)` | `PRIMARY KEY` | UUIDv4 identifier |
| `project_id` | `VARCHAR(36)` | `FK -> projects.id` | Associated project ID |
| `commit_sha` | `VARCHAR(64)` | `NULLABLE` | Git commit SHA assessed |
| `target_type` | `VARCHAR(50)` | `DEFAULT 'github_repository'`| `github_repository` or `local_directory` |
| `status` | `VARCHAR(50)` | `DEFAULT 'queued'` | `queued`, `running`, `completed`, `failed` |
| `readiness_status` | `VARCHAR(50)` | `DEFAULT 'NOT PRODUCTION READY'` | `NOT PRODUCTION READY`, `NEEDS REMEDIATION`, `VERIFIED WITH GAPS` |
| `blockers_count` | `INTEGER` | `DEFAULT 0` | Critical + High severity findings count |
| `total_findings_count` | `INTEGER` | `DEFAULT 0` | Total defect count |
| `verified_controls_count` | `INTEGER` | `DEFAULT 0` | Controls proven clean in ASVS ledger |
| `unverified_gaps_count` | `INTEGER` | `DEFAULT 0` | Controls requiring runtime/dynamic tests |
| `html_report_path` | `VARCHAR(512)` | `NULLABLE` | Local path to rendered HTML audit report |
| `json_report_path` | `VARCHAR(512)` | `NULLABLE` | Local path to structured JSON data |
| `reviewer_name` | `VARCHAR(255)` | `NULLABLE` | Human auditor name ($299 package) |
| `reviewer_status` | `VARCHAR(50)` | `DEFAULT 'pending'` | `pending`, `approved`, `changes_requested` |
| `reviewer_notes` | `TEXT` | `NULLABLE` | Auditor advice for client stakeholders |
| `created_at` | `DATETIME` | `DEFAULT UTC` | Assessment initiation timestamp |
| `completed_at` | `DATETIME` | `NULLABLE` | Scan completion timestamp |

*Relationships:* `findings`, `verification_items`, `audit_events` (1-to-many, cascade delete).

---

### Table: `findings`
Actionable security and configuration defects.
| Column | Type | Constraints | Description |
| :--- | :--- | :--- | :--- |
| `id` | `VARCHAR(36)` | `PRIMARY KEY` | UUIDv4 identifier |
| `assessment_id` | `VARCHAR(36)` | `FK -> assessments.id` | Assessment reference |
| `rule_id` | `VARCHAR(50)` | `NOT NULL` | Rule identifier (e.g. `PR-RLS-001`) |
| `asvs_id` | `VARCHAR(20)` | `NOT NULL` | OWASP ASVS 5.0 section (e.g. `V4.1`) |
| `severity` | `VARCHAR(20)` | `NOT NULL` | `critical`, `high`, `medium`, `low`, `info` |
| `title` | `VARCHAR(255)` | `NOT NULL` | Human-readable title |
| `location` | `VARCHAR(512)` | `NOT NULL` | Relative file path |
| `line` | `INTEGER` | `NULLABLE` | 1-based source code line number |
| `evidence` | `TEXT` | `NOT NULL` | Concrete evidence (secrets redacted) |
| `remediation` | `TEXT` | `NOT NULL` | Plain-English fix instructions |
| `remediation_diff` | `TEXT` | `NULLABLE` | Syntactically valid patch diff |
| `status` | `VARCHAR(50)` | `DEFAULT 'OPEN'` | `OPEN`, `RESOLVED`, `ACCEPTED_RISK` |
| `resolution_notes` | `TEXT` | `NULLABLE` | Developer justification or fix record |
| `resolved_at` | `DATETIME` | `NULLABLE` | Timestamp of status change |

---

### Table: `verification_items`
The **OWASP ASVS 5.0 Verification & Gap Ledger**.
| Column | Type | Constraints | Description |
| :--- | :--- | :--- | :--- |
| `id` | `VARCHAR(36)` | `PRIMARY KEY` | UUIDv4 identifier |
| `assessment_id` | `VARCHAR(36)` | `FK -> assessments.id` | Assessment reference |
| `asvs_id` | `VARCHAR(20)` | `NOT NULL` | ASVS Requirement (e.g. `V1.1`, `V4.1`, `V14.1`) |
| `category` | `VARCHAR(100)` | `NOT NULL` | ASVS domain name |
| `requirement` | `TEXT` | `NOT NULL` | Formal verification statement |
| `status` | `VARCHAR(50)` | `NOT NULL` | `verified_pass`, `finding_fail`, `unverified_gap` |
| `verification_method` | `VARCHAR(100)` | `NOT NULL` | `static_filesystem`, `static_regex`, `static_ast`, `manual_review_required` |
| `evidence_or_reason` | `TEXT` | `NOT NULL` | Proof of test execution or justification for gap |

---

### Table: `audit_events`
Immutable log of assessment lifecycle, finding modifications, and human sign-offs.
| Column | Type | Constraints | Description |
| :--- | :--- | :--- | :--- |
| `id` | `VARCHAR(36)` | `PRIMARY KEY` | UUIDv4 identifier |
| `assessment_id` | `VARCHAR(36)` | `FK -> assessments.id` | Assessment reference |
| `event_type` | `VARCHAR(100)` | `NOT NULL` | `scan_completed`, `finding_status_updated`, `reassessment_requested` |
| `actor` | `VARCHAR(255)` | `DEFAULT 'system'` | User email, API token, or system identifier |
| `payload_json` | `TEXT` | `NULLABLE` | Structured event metadata |
| `created_at` | `DATETIME` | `DEFAULT UTC` | Timestamp |

---

## 3. Verified API Endpoints

All endpoints have been tested and verified via `backend/scripts/verify_e2e.py`:

| Method | Endpoint | Description | Sample Status |
| :--- | :--- | :--- | :--- |
| `GET` | `/api/health` | Service health status | `200 OK` |
| `POST` | `/api/projects` | Register a new repository | `201 Created` |
| `GET` | `/api/projects` | List all projects & latest statuses | `200 OK` |
| `GET` | `/api/projects/{id}` | Retrieve project by ID | `200 OK` |
| `DELETE` | `/api/projects/{id}` | Delete project & cascade assessments | `204 No Content` |
| `POST` | `/api/projects/{id}/assessments` | Trigger ephemeral assessment | `201 Created` |
| `GET` | `/api/projects/{id}/assessments` | List assessment history for project | `200 OK` |
| `GET` | `/api/assessments/{id}` | Full assessment detail, findings & ledger | `200 OK` |
| `GET` | `/api/assessments/{id}/report.html` | Download executive HTML report | `200 OK` |
| `GET` | `/api/assessments/{id}/report.json` | Download machine-readable JSON data | `200 OK` |
| `PATCH` | `/api/findings/{id}/status` | Update finding status (`RESOLVED`, etc.) | `200 OK` |
| `POST` | `/api/assessments/{id}/review` | Apply reviewer sign-off ($299 package) | `200 OK` |
| `POST` | `/api/assessments/{id}/reassessment` | Trigger clean re-scan cycle | `200 OK` |
| `POST` | `/api/webhooks/github` | Ingest GitHub App push & PR webhooks | `200 OK` |

---

## 4. Setup & Running Instructions

### Step 1: Backend Setup (FastAPI Orchestrator)

1. Navigate to the backend directory:
   ```bash
   cd backend
   ```

2. Configure environment (copy example):
   ```bash
   cp .env.example .env
   ```

3. Run the complete automated End-to-End verification suite:
   ```bash
   python scripts/verify_e2e.py
   ```
   *Expected output: `ALL END-TO-END VERIFICATION CHECKS PASSED SUCCESSFULLY (13/13 ENDPOINTS)`*

4. Run unit tests:
   ```bash
   python -m unittest discover -s tests -v
   ```

5. Launch the development server:
   ```bash
   python -m uvicorn app.main:app --reload --port 8000
   ```
   - API Docs / Swagger: `http://localhost:8000/docs`
   - Health check: `http://localhost:8000/api/health`

---

### Step 2: Frontend Setup (Next.js 15 Dashboard)

1. Navigate to the frontend directory:
   ```bash
   cd ../frontend
   ```

2. Configure environment:
   ```bash
   cp .env.example .env.local
   ```

3. Install dependencies and start development server:
   ```bash
   npm install
   npm run dev
   ```

4. Open `http://localhost:3000` in your browser.
   - **`/`**: Projects Interface (connect repositories and view audit statuses).
   - **`/assessments/[id]`**: Assessments Interface (Scorecard, ASVS 5.0 Ledger, Auditor Stamp).
   - **`/remediation/[id]`**: Remediation Workspace (Diff viewer, mark resolved, request reassessment).

---

### Step 3: Standalone Engine CLI (`productionready_starter`)

To inspect a local directory or remote repository directly from the terminal without starting the database:

```bash
cd productionready_starter

# Run tests
python -m unittest discover -s tests -v

# Inspect local directory
python -m productionready /path/to/project --output local-audit

# Inspect remote GitHub repository (ephemeral, zero code stored)
python -m productionready https://github.com/owner/repo --output remote-audit

# Generate $299 human-reviewed package with auditor credentials
python -m productionready /path/to/project \
  --reviewer "Jane Doe, Lead AppSec Auditor" \
  --notes "Audited against OWASP ASVS 5.0. All launch blockers resolved." \
  --output final-audit
```
