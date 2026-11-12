"""Integration tests for ProductionReady FastAPI endpoints and workflows."""
import tempfile
import unittest
from pathlib import Path
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.main import app
from app.database import Base, get_db

# In-memory test SQLite engine with StaticPool so all threads/sessions share the same memory DB
from sqlalchemy.pool import StaticPool

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


class ApiTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        Base.metadata.create_all(bind=engine)
        cls.client = TestClient(app)

    @classmethod
    def tearDownClass(cls):
        Base.metadata.drop_all(bind=engine)

    def test_01_health_check(self):
        resp = self.client.get("/api/health")
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertEqual(data["status"], "healthy")

    def test_02_project_lifecycle_and_assessment(self):
        # Create a sample project directory with a known flaw
        with tempfile.TemporaryDirectory() as td:
            p = Path(td)
            (p / "package.json").write_text("{}", encoding="utf-8")
            (p / "settings.py").write_text("DEBUG = True\nSECRET_KEY = 'changeme'\n", encoding="utf-8")
            (p / "schema.sql").write_text("CREATE TABLE users (id int);\n", encoding="utf-8")

            # 1. Create Project
            proj_resp = self.client.post(
                "/api/projects",
                json={
                    "name": "Acme SaaS MVP",
                    "repository_url": str(p),
                    "default_branch": "main",
                },
            )
            self.assertEqual(proj_resp.status_code, 201)
            project_id = proj_resp.json()["id"]

            # 2. Trigger Assessment
            scan_resp = self.client.post(
                f"/api/projects/{project_id}/assessments",
                json={"ref": "main"},
            )
            self.assertEqual(scan_resp.status_code, 201)
            assessment_data = scan_resp.json()
            assessment_id = assessment_data["id"]
            self.assertEqual(assessment_data["status"], "completed")
            self.assertEqual(assessment_data["readiness_status"], "NOT PRODUCTION READY")
            self.assertTrue(assessment_data["blockers_count"] > 0)

            # 3. Retrieve Assessment Details
            detail_resp = self.client.get(f"/api/assessments/{assessment_id}")
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
                json={
                    "status": "RESOLVED",
                    "resolution_notes": "Rotated secret and stored in AWS Secrets Manager.",
                },
            )
            self.assertEqual(patch_resp.status_code, 200)
            self.assertEqual(patch_resp.json()["status"], "RESOLVED")

            # 5. Apply Reviewer Sign-Off ($299 Package)
            review_resp = self.client.post(
                f"/api/assessments/{assessment_id}/review",
                json={
                    "reviewer_name": "Lead Auditor",
                    "reviewer_status": "changes_requested",
                    "reviewer_notes": "Fix remaining Supabase RLS before launch.",
                },
            )
            self.assertEqual(review_resp.status_code, 200)
            self.assertEqual(review_resp.json()["reviewer_name"], "Lead Auditor")

            # 6. Fetch HTML Report
            html_resp = self.client.get(f"/api/assessments/{assessment_id}/report.html")
            self.assertEqual(html_resp.status_code, 200)
            self.assertIn("ProductionReady", html_resp.text)
            self.assertIn("OWASP ASVS 5.0 Verification", html_resp.text)


if __name__ == "__main__":
    unittest.main()
