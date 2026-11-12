"""Integration tests for ProductionReady FastAPI endpoints, security controls, and workflows."""
import hashlib
import hmac
import json
import sys
import tempfile
import unittest
from pathlib import Path

# Ensure backend root is on sys.path
BACKEND_ROOT = Path(__file__).resolve().parent.parent
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.main import app
from app.database import Base, get_db
from app.config import settings

TEST_DB_URL = "sqlite:///:memory:"
engine = create_engine(
    TEST_DB_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db


class ApiSecurityAndWorkflowTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        Base.metadata.create_all(bind=engine)
        cls.client = TestClient(app)
        cls.valid_headers = {"X-API-Key": settings.effective_api_key}

    @classmethod
    def tearDownClass(cls):
        Base.metadata.drop_all(bind=engine)

    def test_01_health_check_unauthenticated(self):
        """Health check endpoint should be publicly accessible without credentials."""
        resp = self.client.get("/api/health")
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertEqual(data["status"], "healthy")

    def test_02_authentication_enforcement(self):
        """Protected endpoints must reject requests without valid credentials."""
        # Unauthenticated request
        resp_unauth = self.client.get("/api/projects")
        self.assertEqual(resp_unauth.status_code, 401)
        self.assertIn("Missing authentication credentials", resp_unauth.json()["detail"])

        # Invalid API key
        resp_bad_key = self.client.get("/api/projects", headers={"X-API-Key": "invalid_bogus_key"})
        self.assertEqual(resp_bad_key.status_code, 401)
        self.assertIn("Invalid API key", resp_bad_key.json()["detail"])

        # Valid Bearer token authentication
        resp_bearer = self.client.get(
            "/api/projects",
            headers={"Authorization": f"Bearer {settings.effective_api_key}"},
        )
        self.assertEqual(resp_bearer.status_code, 200)

        # Valid X-API-Key authentication
        resp_key = self.client.get("/api/projects", headers=self.valid_headers)
        self.assertEqual(resp_key.status_code, 200)

    def test_03_project_lifecycle_and_assessments(self):
        """End-to-end test of project creation, synchronous scan, remediation, and report generation."""
        with tempfile.TemporaryDirectory() as td:
            p = Path(td)
            (p / "package.json").write_text("{}", encoding="utf-8")
            (p / "settings.py").write_text("DEBUG = True\nSECRET_KEY = 'changeme'\n", encoding="utf-8")
            (p / "schema.sql").write_text("CREATE TABLE users (id int);\n", encoding="utf-8")

            # 1. Create Project
            proj_resp = self.client.post(
                "/api/projects",
                headers=self.valid_headers,
                json={
                    "name": "Fintech Alpha Service",
                    "repository_url": str(p),
                    "default_branch": "main",
                },
            )
            self.assertEqual(proj_resp.status_code, 201)
            project_id = proj_resp.json()["id"]

            # 2. Trigger Synchronous Assessment (sync=true)
            scan_resp = self.client.post(
                f"/api/projects/{project_id}/assessments?sync=true",
                headers=self.valid_headers,
                json={"ref": "main"},
            )
            self.assertEqual(scan_resp.status_code, 202)
            assessment_data = scan_resp.json()
            assessment_id = assessment_data["id"]
            self.assertEqual(assessment_data["status"], "completed")
            self.assertEqual(assessment_data["readiness_status"], "NOT PRODUCTION READY")
            self.assertTrue(assessment_data["blockers_count"] > 0)

            # 3. Retrieve Assessment Details
            detail_resp = self.client.get(f"/api/assessments/{assessment_id}", headers=self.valid_headers)
            self.assertEqual(detail_resp.status_code, 200)
            detail = detail_resp.json()
            findings = detail["findings"]
            ledger = detail["verification_items"]

            self.assertTrue(len(findings) > 0)
            self.assertTrue(len(ledger) > 0)

            # Check that RLS and SECRET_KEY defects were identified
            rule_ids = {f["rule_id"] for f in findings}
            self.assertIn("PR-SECRET-001", rule_ids)
            self.assertIn("PR-RLS-001", rule_ids)

            # 4. Update Finding Status (Remediation Workflow)
            secret_finding = next(f for f in findings if f["rule_id"] == "PR-SECRET-001")
            patch_resp = self.client.patch(
                f"/api/findings/{secret_finding['id']}/status",
                headers=self.valid_headers,
                json={
                    "status": "RESOLVED",
                    "resolution_notes": "Rotated secret and stored in AWS Secrets Manager.",
                },
            )
            self.assertEqual(patch_resp.status_code, 200)
            self.assertEqual(patch_resp.json()["status"], "RESOLVED")

            # 5. Apply Reviewer Sign-Off ($299 Package Deliverable)
            review_resp = self.client.post(
                f"/api/assessments/{assessment_id}/review",
                headers=self.valid_headers,
                json={
                    "reviewer_name": "Lead Security Auditor",
                    "reviewer_status": "changes_requested",
                    "reviewer_notes": "Fix remaining Supabase RLS before launch.",
                },
            )
            self.assertEqual(review_resp.status_code, 200)
            self.assertEqual(review_resp.json()["reviewer_name"], "Lead Security Auditor")

            # 6. Fetch HTML and JSON Reports
            html_resp = self.client.get(f"/api/assessments/{assessment_id}/report.html", headers=self.valid_headers)
            self.assertEqual(html_resp.status_code, 200)
            self.assertIn("ProductionReady", html_resp.text)
            self.assertIn("OWASP ASVS 5.0 Verification", html_resp.text)

            json_resp = self.client.get(f"/api/assessments/{assessment_id}/report.json", headers=self.valid_headers)
            self.assertEqual(json_resp.status_code, 200)

            # 7. Trigger Asynchronous Background Assessment
            async_scan_resp = self.client.post(
                f"/api/projects/{project_id}/assessments",
                headers=self.valid_headers,
                json={"ref": "main"},
            )
            self.assertEqual(async_scan_resp.status_code, 202)
            self.assertIn(async_scan_resp.json()["status"], ("queued", "completed"))

    def test_04_webhook_signature_enforcement(self):
        """Webhook endpoint must strictly reject unauthenticated or incorrectly signed payloads."""
        payload = json.dumps({"repository": {"html_url": "https://github.com/org/sample"}}).encode("utf-8")

        # 1. Unsigned webhook should be rejected (401)
        resp_unsigned = self.client.post(
            "/api/webhooks/github",
            content=payload,
            headers={"X-GitHub-Event": "push"},
        )
        self.assertEqual(resp_unsigned.status_code, 401)

        # 2. Webhook with wrong signature should be rejected (401)
        resp_bad_sig = self.client.post(
            "/api/webhooks/github",
            content=payload,
            headers={
                "X-GitHub-Event": "push",
                "X-Hub-Signature-256": "sha256=0000000000000000000000000000000000000000000000000000000000000000",
            },
        )
        self.assertEqual(resp_bad_sig.status_code, 401)

        # 3. Webhook with valid signature (when configured) is accepted
        test_secret = "test_webhook_signing_secret_9988"
        original_secret = settings.GITHUB_WEBHOOK_SECRET
        settings.GITHUB_WEBHOOK_SECRET = test_secret
        try:
            valid_sig = hmac.new(test_secret.encode("utf-8"), payload, hashlib.sha256).hexdigest()
            resp_valid_sig = self.client.post(
                "/api/webhooks/github",
                content=payload,
                headers={
                    "X-GitHub-Event": "push",
                    "X-Hub-Signature-256": f"sha256={valid_sig}",
                },
            )
            self.assertEqual(resp_valid_sig.status_code, 200)
            self.assertEqual(resp_valid_sig.json()["event"], "push")
        finally:
            settings.GITHUB_WEBHOOK_SECRET = original_secret


if __name__ == "__main__":
    unittest.main()
