import sys
import tempfile
import unittest
from pathlib import Path

# Ensure package root is in sys.path
PACKAGE_ROOT = Path(__file__).resolve().parent.parent
if str(PACKAGE_ROOT) not in sys.path:
    sys.path.insert(0, str(PACKAGE_ROOT))

from productionready.scanner import scan, render_html
from productionready.intake import parse_github_spec


class ScanTests(unittest.TestCase):
    def test_detects_private_key_and_debug(self):
        with tempfile.TemporaryDirectory() as td:
            p = Path(td)
            (p / "settings.py").write_text("DEBUG=true\n" + "-----BEGIN " + "PRIVATE KEY-----\n", encoding="utf-8")
            r = scan(p)
            ids = {x["rule_id"] for x in r["findings"]}
            self.assertIn("PR-KEY-001", ids)
            self.assertIn("PR-DEBUG-001", ids)
            html = render_html(r)
            self.assertNotIn("PRIVATE KEY-----", html.split("Findings (")[1].split("Checks performed")[0])

    def test_ignores_vendor_and_not_claim_safe(self):
        with tempfile.TemporaryDirectory() as td:
            p = Path(td)
            (p / "node_modules").mkdir()
            (p / "node_modules" / "a.py").write_text("DEBUG=true", encoding="utf-8")
            r = scan(p)
            self.assertEqual(r["status"], "partial_static_review_only")
            self.assertFalse(any(x["rule_id"] == "PR-DEBUG-001" for x in r["findings"]))

    def test_detects_supabase_rls_missing(self):
        with tempfile.TemporaryDirectory() as td:
            p = Path(td)
            migration = (
                "CREATE TABLE public.organizations (\n"
                "    id UUID PRIMARY KEY,\n"
                "    name TEXT NOT NULL\n"
                ");\n"
            )
            (p / "001_init.sql").write_text(migration, encoding="utf-8")
            r = scan(p)
            ids = {x["rule_id"] for x in r["findings"]}
            self.assertIn("PR-RLS-001", ids)
            rls_finding = next(f for f in r["findings"] if f["rule_id"] == "PR-RLS-001")
            self.assertIn("organizations", rls_finding["title"])
            self.assertIsNotNone(rls_finding["remediation_diff"])

    def test_detects_client_side_service_role_leak(self):
        with tempfile.TemporaryDirectory() as td:
            p = Path(td)
            (p / "client.ts").write_text(
                'const key = process.env.' + 'NEXT_PUBLIC_' + 'SUPABASE_SERVICE_ROLE_KEY;\n',
                encoding="utf-8",
            )
            r = scan(p)
            ids = {x["rule_id"] for x in r["findings"]}
            self.assertIn("PR-CLIENT-001", ids)
            self.assertEqual(r["readiness_status"], "NOT PRODUCTION READY")

    def test_detects_unverified_stripe_webhook(self):
        with tempfile.TemporaryDirectory() as td:
            p = Path(td)
            (p / "webhook.ts").write_text(
                "export async function POST(req) {\n"
                "  const event = await req.json();\n"
                "  if (event.type === 'checkout.session.completed') { grantAccess(); }\n"
                "}\n",
                encoding="utf-8",
            )
            r = scan(p)
            ids = {x["rule_id"] for x in r["findings"]}
            self.assertIn("PR-PAY-001", ids)

    def test_verification_ledger_generation(self):
        with tempfile.TemporaryDirectory() as td:
            p = Path(td)
            (p / "package.json").write_text("{}", encoding="utf-8")
            (p / "tests").mkdir()
            r = scan(p)
            ledger = r["verification_ledger"]
            self.assertTrue(len(ledger) > 0)
            
            # Manifest (V1.1) and tests (V1.2) should be verified_pass
            statuses = {item["asvs_id"]: item["status"] for item in ledger}
            self.assertEqual(statuses.get("V1.1"), "verified_pass")
            self.assertEqual(statuses.get("V1.2"), "verified_pass")
            
            # Threat modeling (V1.3) and backup restore (V14.2) should be unverified_gap
            self.assertEqual(statuses.get("V1.3"), "unverified_gap")
            self.assertEqual(statuses.get("V14.2"), "unverified_gap")

    def test_reviewer_signoff_support(self):
        with tempfile.TemporaryDirectory() as td:
            p = Path(td)
            (p / "package.json").write_text("{}", encoding="utf-8")
            (p / "tests").mkdir()
            r = scan(p, reviewer_name="Alex Security", reviewer_notes="Pre-launch verification approved.")
            self.assertEqual(r["reviewer_sign_off"]["reviewer_name"], "Alex Security")
            self.assertEqual(r["reviewer_sign_off"]["notes"], "Pre-launch verification approved.")

    def test_github_intake_url_parser(self):
        owner, repo = parse_github_spec("https://github.com/my-org/my-ai-app")
        self.assertEqual(owner, "my-org")
        self.assertEqual(repo, "my-ai-app")

        owner2, repo2 = parse_github_spec("agency/client-portal.git")
        self.assertEqual(owner2, "agency")
        self.assertEqual(repo2, "client-portal")


if __name__ == "__main__":
    unittest.main()
