# ProductionReady v0.2 — Evidence-Backed Security Verification & Remediation Engine

ProductionReady audits applications built with Cursor, Claude Code, Lovable, Bolt, and Replit before they go to production.

Instead of treating scanner silence as safety, ProductionReady implements a strict **Three-State Verification Model**:
1. **Verified Clean**: Security controls actively tested and proven compliant.
2. **Finding Defect**: Actionable defects with location, evidence, and copy-paste remediation diffs.
3. **Unverified Gap**: Operational surfaces requiring dynamic testing, cloud infrastructure audits, or manual penetration checks.

---

## Quickstart

Requires Python 3.10+. Zero third-party Python dependencies required.

### 1. Scan a local directory

```bash
cd productionready_starter
python -m productionready /path/to/your/app --output my-audit
```

### 2. Ephemeral GitHub Intake (Zero Code Retention)

Inspect a remote public or private GitHub repository without cloning or storing code permanently:

```bash
# Public repo
python -m productionready https://github.com/owner/repo --output audit-report

# Private repo with GitHub Personal Access Token
python -m productionready owner/repo --github-token ghp_yourTokenHere --ref main
```

### 3. Generate a $299 Human-Reviewed Assessment Package

Add auditor verification credentials and notes to the executive report:

```bash
python -m productionready /path/to/app \
  --reviewer "Jane Doe, Lead AppSec Auditor" \
  --notes "Audited for launch against OWASP ASVS 5.0 baseline. Passed all blockers." \
  --output client-deliverable
```

Generates:
- `client-deliverable.html`: Executive deployment readiness report, scorecard, findings with diffs, ASVS 5.0 ledger, and auditor verification stamp.
- `client-deliverable.json`: Machine-readable assessment data for CI/CD or dashboard ingestion.

---

## Test Suite

Run the full automated test suite:

```bash
python -m unittest discover -s tests -v
```

---

## Active Verification Rules

| Rule ID | ASVS 5.0 | Category | Description |
| :--- | :--- | :--- | :--- |
| `PR-KEY-001` | V8.1 | Cryptography | Private key headers (PEM, RSA, OpenSSH, EC) |
| `PR-SECRET-001` | V2.1 | Authentication | Predictable application secrets |
| `PR-APIKEY-001` | V2.1 | Credentials | Hardcoded SaaS & AI platform keys (OpenAI, Anthropic, Stripe, AWS, Resend, GitHub) |
| `PR-CLIENT-001` | V4.2 | Access Control | High-privilege database secrets leaked to client bundles (`NEXT_PUBLIC_*_SERVICE_ROLE`) |
| `PR-RLS-001` | V4.1 | Database | Supabase / PostgreSQL tables created without Row Level Security |
| `PR-PAY-001` | V5.1 | Validation | Stripe/payment webhook endpoints missing cryptographic signature validation |
| `PR-DEBUG-001` | V14.1 | Configuration | Enabled debug and development flags |
| `PR-CORS-001` | V13.1 | API | Insecure CORS wildcard with credentials enabled |
| `PR-ENV-001` | V8.2 | Environment | Active `.env` files present in source code |
| `PR-MANIFEST-001`| V1.1 | Architecture | Dependency manifest tracking (SBOM) |
| `PR-TEST-001` | V1.2 | Architecture | Conventional automated test suite presence |
| `PR-GIT-001` | V14.1 | Hygiene | Missing `.gitignore` configuration |

---

## OWASP ASVS 5.0 Verification & Gap Ledger

Every report produces an explicit ledger separating verified controls from unverified surfaces (e.g., dynamic password hashing tests, database disaster recovery tests, and session cookie inspection in production).
