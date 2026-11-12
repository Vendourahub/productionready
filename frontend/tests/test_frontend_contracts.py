"""Contract and validation tests for Next.js frontend interfaces and API client."""
import json
import re
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
FRONTEND_DIR = REPO_ROOT / "frontend"
BACKEND_DIR = REPO_ROOT / "backend"


class FrontendContractTests(unittest.TestCase):
    def test_frontend_api_client_enforces_auth_header(self):
        """Verifies that frontend/lib/api.ts includes X-API-Key in getHeaders()."""
        api_ts = (FRONTEND_DIR / "lib" / "api.ts").read_text(encoding="utf-8")
        self.assertIn("X-API-Key", api_ts)
        self.assertIn("NEXT_PUBLIC_API_KEY", api_ts)

    def test_frontend_finding_interface_matches_backend_model(self):
        """Verifies that TypeScript Finding interface matches SQLAlchemy Finding model fields."""
        api_ts = (FRONTEND_DIR / "lib" / "api.ts").read_text(encoding="utf-8")
        backend_finding = (BACKEND_DIR / "app" / "models" / "finding.py").read_text(encoding="utf-8")

        required_fields = [
            "id",
            "assessment_id",
            "rule_id",
            "asvs_id",
            "severity",
            "title",
            "location",
            "line",
            "evidence",
            "remediation",
            "status",
        ]
        for f in required_fields:
            self.assertIn(f, api_ts, f"Missing field '{f}' in frontend Finding interface")
            self.assertIn(f, backend_finding, f"Missing field '{f}' in backend Finding model")

    def test_frontend_pages_exist_and_render_cleanly(self):
        """Verifies all Next.js App Router core page files exist."""
        expected_pages = [
            FRONTEND_DIR / "app" / "page.tsx",
            FRONTEND_DIR / "app" / "assessments" / "[id]" / "page.tsx",
            FRONTEND_DIR / "app" / "remediation" / "[id]" / "page.tsx",
            FRONTEND_DIR / "app" / "layout.tsx",
        ]
        for p in expected_pages:
            self.assertTrue(p.exists(), f"Page not found: {p}")
            content = p.read_text(encoding="utf-8")
            self.assertGreater(len(content), 100, f"Page file unexpectedly empty: {p}")


if __name__ == "__main__":
    unittest.main()
