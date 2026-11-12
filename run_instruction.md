# ProductionReady Platform — Run & Build Instructions

This document provides reproducible, step-by-step instructions to install, configure, build, run, and test the **ProductionReady** verification and remediation platform.

---

## 1. Prerequisites

Ensure the following runtimes and tools are installed:
- **Python**: `v3.10` or higher (verified with `v3.10`, `v3.11`, `v3.12`, `v3.14`)
- **Node.js**: `v20.x` or higher (verified with `v20.x` / `v24.x`)
- **npm**: `v10.x` or higher
- **Database**: SQLite (built into Python for zero-setup local dev) or PostgreSQL `v14+` for production

Verify runtimes in your terminal:
```bash
python --version
node -v
npm -v
```

---

## 2. Environment Setup

### Backend Environment:
1. Navigate to the backend directory and copy the template configuration:
   ```bash
   cd backend
   cp .env.example .env
   ```

2. Key configuration variables:
   - `DATABASE_URL`: `sqlite:///./productionready.db` (or `postgresql://user:password@localhost:5432/productionready`)
   - `GITHUB_APP_ID`: *(Optional)* GitHub App ID for automated webhook intake
   - `GITHUB_WEBHOOK_SECRET`: *(Optional)* Webhook secret for HMAC-SHA256 signature verification

### Frontend Environment:
1. Navigate to the frontend directory:
   ```bash
   cd ../frontend
   cp .env.example .env.local
   ```
2. Key configuration variables:
   - `NEXT_PUBLIC_API_URL`: `http://localhost:8000` (points to the FastAPI orchestrator)

---

## 3. Dependency Installation & Database Setup

### Backend Dependencies & Migrations:
```bash
cd backend
pip install -r requirements.txt
alembic upgrade head
```
*(Dependencies: `fastapi`, `uvicorn`, `sqlalchemy`, `alembic`, `pydantic`, `httpx`).*

### Frontend Dependencies:
```bash
cd ../frontend
npm install
```

---

## 4. Build & Compilation

To build the Next.js production frontend bundle:

```bash
cd frontend
npm run build
```

---

## 5. Running the Application

### Step A: Start the FastAPI Orchestrator (Backend)
```bash
cd backend
python -m uvicorn app.main:app --reload --port 8000
```
- API Base: [http://localhost:8000](http://localhost:8000)
- Interactive OpenAPI / Swagger UI: [http://localhost:8000/docs](http://localhost:8000/docs)
- Health check: [http://localhost:8000/api/health](http://localhost:8000/api/health)

### Step B: Start the Next.js Dashboard (Frontend)
```bash
cd frontend
npm run dev
```
Open your browser at [http://localhost:3000](http://localhost:3000).
- **`/`**: Projects Interface (connect repositories and view audit statuses)
- **`/assessments/[id]`**: Assessments Interface (Readiness Scorecard, ASVS 5.0 Ledger, Auditor Stamp)
- **`/remediation/[id]`**: Remediation Workspace (Diff viewer, mark resolved, request reassessment)

---

## 6. Running the Automated Test Suite

Execute the complete multi-tier test suites:

### 1. Standalone Core Inspection Engine & Security Intake Tests:
```bash
python -m unittest discover -s productionready_starter/tests -v
```
*(Tests Supabase RLS detection, client leak detection, Stripe webhook validation, and tarball symlink/path traversal defenses).*

### 2. Backend API Security & Integration Tests:
```bash
python -m unittest discover -s backend/tests -v
```
*(Tests API Key authentication, webhook HMAC enforcement, background task queueing, and reviewer sign-off).*

### 3. Frontend Contract Tests:
```bash
python frontend/tests/test_frontend_contracts.py
```
*(Validates frontend TypeScript API contracts and payload interfaces).*

### 4. Full Live 13-Endpoint End-to-End Verification:
```bash
python backend/scripts/verify_e2e.py
```
*Executes all 13 REST API endpoints, verifies database tables, tests finding lifecycle, and generates audit reports.*
