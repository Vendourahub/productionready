"""Database and Row Level Security (RLS) inspection rules."""
from __future__ import annotations
import re
from pathlib import Path
from typing import List
from ..models import Finding, Severity

# Pattern for detecting table creation in SQL migrations
CREATE_TABLE_RE = re.compile(
    r"(?i)create\s+table(?:\s+if\s+not\s+exists)?\s+(?:public\.)?[\"']?([a-zA-Z0-9_]+)[\"']?",
    re.MULTILINE
)

# Pattern for detecting ALTER TABLE ... ENABLE ROW LEVEL SECURITY
ENABLE_RLS_RE = re.compile(
    r"(?i)alter\s+table(?:\s+only)?\s+(?:public\.)?[\"']?([a-zA-Z0-9_]+)[\"']?\s+enable\s+row\s+level\s+security",
    re.MULTILINE
)


def inspect_sql_rls(rel_path: str, content: str) -> List[Finding]:
    """Inspects SQL migration files to ensure created tables have Row Level Security enabled."""
    findings: List[Finding] = []
    
    # Only inspect SQL files or migrations
    if not (rel_path.endswith(".sql") or "migration" in rel_path.lower()):
        return findings

    created_tables = set(CREATE_TABLE_RE.findall(content))
    rls_enabled_tables = set(ENABLE_RLS_RE.findall(content))

    # Identify tables missing RLS
    unprotected = created_tables - rls_enabled_tables
    # Exclude standard meta tables like migrations
    unprotected = {t for t in unprotected if not t.startswith("_") and t not in {"schema_migrations", "spatial_ref_sys", "supabase_migrations"}}

    for table in sorted(unprotected):
        # Locate line number of CREATE TABLE
        line_num = 1
        for idx, line in enumerate(content.splitlines(), 1):
            if re.search(rf"(?i)create\s+table.*{table}", line):
                line_num = idx
                break

        findings.append(
            Finding(
                rule_id="PR-RLS-001",
                asvs_id="V4.1",
                severity=Severity.HIGH.value,
                title=f"Database table '{table}' created without Row Level Security (RLS)",
                location=rel_path,
                line=line_num,
                evidence=f"Table '{table}' has no corresponding 'ALTER TABLE ... ENABLE ROW LEVEL SECURITY;' declaration.",
                remediation=(
                    f"Enable RLS on '{table}' to prevent anonymous or cross-tenant access via Supabase/PostgreSQL APIs. "
                    f"Add policy rules granting access only to authorized user IDs."
                ),
                remediation_diff=(
                    f"--- a/{rel_path}\n+++ b/{rel_path}\n"
                    f"+ALTER TABLE public.{table} ENABLE ROW LEVEL SECURITY;\n"
                    f"+CREATE POLICY \"Users can only access own {table}\" ON public.{table}\n"
                    f"+  FOR ALL USING (auth.uid() = user_id);"
                ),
                confidence="high",
            )
        )

    return findings
