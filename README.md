# ProductionReady — Phase 2 Commercial Architecture

Evidence-backed deployment readiness verification and remediation platform for AI-built web applications (Cursor, Claude Code, Lovable, Bolt, Replit).

---

## Architecture Overview

```
productionready/
├── backend/                       # FastAPI Orchestration & Verification Service
│   ├── app/
│   │   ├── main.py                # FastAPI application entrypoint & middleware
│   │   ├── config.py              # Environment configuration & reports dir
│   │   ├── database.py            # SQLAlchemy engine, sessionmaker & Base
│   │   ├── models/                # PostgreSQL / SQLite entities:
│   │   │   ├── project.py         # Project (connected repositories)
│   │   │   ├── assessment.py      # Assessment (readiness score, metrics, timestamps)
│   │   │   ├── finding.py         # Finding (rule_id, ASVS ID, diff, OPEN/RESOLVED status)
│   │   │   ├── verification.py    # ASVS 5.0 Verification & Gap Ledger items
│   │   │   └── audit_event.py     # Audit log for status changes and reassessments
│   │   ├── schemas/               # Pydantic validation models
│   │   ├── services/
│   │   │   ├── runner.py          # Ephemeral intake & multi-rule inspection execution
│   │   │   ├── github.py          # GitHub App webhook HMAC verification
│   │   │   └── remediation.py     # Finding resolution & reassessment workflow
│   │   └── api/
│   │       ├── projects.py        # /api/projects CRUD
│   │       ├── assessments.py     # /api/projects/{id}/assessments & exports
│   │       ├── remediation.py     # /api/findings/{id}/status & reassessments
│   │       └── webhooks.py        # /api/webhooks/github
│   └── tests/                     # Integration tests for API & database workflows
│
├── frontend/                      # Next.js 15 Customer Dashboard (Three Central Interfaces)
│   ├── app/
│   │   ├── page.tsx               # 1. PROJECTS: Connect repos, branch picker, run audit
│   │   ├── assessments/[id]/      # 2. ASSESSMENTS: Executive Scorecard, ASVS 5.0 Ledger, Auditor Stamp
│   │   └── remediation/[id]/      # 3. REMEDIATION: Findings workspace, diffs, resolution & re-scan
│   ├── components/                # Scorecard, VerificationLedger, FindingCard, Navbar
│   └── lib/api.ts                 # Typed API client for FastAPI backend
│
└── productionready_starter/       # Core static inspection and rule execution engine (v0.2)
```

---

## The Three Central Interfaces

1. **Projects (`/`)**:
   Connect an authorized GitHub repository (`https://github.com/owner/repo`) or local path. Select a branch or commit, view historical assessment statuses, and trigger one-click audits.

2. **Assessments (`/assessments/[id]`)**:
   Executive deployment readiness scorecard with red/amber/green verdict, blocker counts, downloadable executive HTML and JSON reports, full **OWASP ASVS 5.0 Verification & Gap Ledger**, and the **\$299 Human Auditor Verification Stamp**.

3. **Remediation (`/remediation/[id]`)**:
   Prioritized remediation action plan. Review exact code locations, redacted evidence, copy-pasteable remediation diffs, mark issues as `RESOLVED` or `ACCEPTED_RISK`, and request one-click clean reassessments.

---

## Running the Platform Locally

### 1. Start the FastAPI Orchestrator (Backend)

```bash
cd backend
python -m uvicorn app.main:app --reload --port 8000
```

- API Base: `http://localhost:8000`
- Interactive OpenAPI / Swagger Docs: `http://localhost:8000/docs`
- Health check: `http://localhost:8000/api/health`

Run backend integration tests:
```bash
python -m unittest discover -s tests -v
```

### 2. Start the Customer Dashboard (Frontend)

```bash
cd frontend
npm install
npm run dev
```

Open `http://localhost:3000` in your browser.

---

## GitHub App Intake & Webhooks

Set the following environment variables in `backend/.env` for GitHub App production deployment:

```env
DATABASE_URL=postgresql://user:password@localhost:5432/productionready
GITHUB_APP_ID=your_app_id
GITHUB_WEBHOOK_SECRET=your_webhook_secret
GITHUB_PRIVATE_KEY_PATH=/path/to/private-key.pem
```

The intake endpoint `POST /api/webhooks/github` automatically validates HMAC SHA256 signatures and schedules ephemeral, zero-storage scans upon commit push.
