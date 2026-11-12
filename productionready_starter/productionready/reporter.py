"""High-polish HTML and JSON report generator for ProductionReady assessments."""
from __future__ import annotations
import json
import os
from html import escape
from typing import Dict, Any
from .models import AssessmentReport


def render_json(report: AssessmentReport) -> str:
    """Serializes the assessment report to formatted JSON."""
    return json.dumps(report.to_dict(), indent=2)


def render_html(report_data: Dict[str, Any]) -> str:
    """Generates an executive-ready, professional HTML deployment readiness report."""
    def e(val: Any) -> str:
        return escape(str(val if val is not None else ""), quote=True)

    summary = report_data.get("summary", {})
    by_sev = summary.get("by_severity", {})
    blockers = by_sev.get("critical", 0) + by_sev.get("high", 0)
    readiness = report_data.get("readiness_status", "NOT PRODUCTION READY")
    
    # Color badge for readiness
    if readiness == "NOT PRODUCTION READY":
        badge_bg = "#dc2626"
        badge_border = "#991b1b"
    elif readiness == "NEEDS REMEDIATION":
        badge_bg = "#d97706"
        badge_border = "#b45309"
    else:
        badge_bg = "#059669"
        badge_border = "#047857"

    findings = report_data.get("findings", [])
    ledger = report_data.get("verification_ledger", [])
    verified_count = sum(1 for item in ledger if item["status"] == "verified_pass")
    gap_count = sum(1 for item in ledger if item["status"] == "unverified_gap")
    failing_count = sum(1 for item in ledger if item["status"] == "finding_fail")

    # Render findings cards
    finding_cards = []
    if findings:
        for f in findings:
            sev = f["severity"].lower()
            sev_colors = {
                "critical": ("#fee2e2", "#991b1b", "#b91c1c"),
                "high": ("#ffedd5", "#9a3412", "#c2410c"),
                "medium": ("#fef9c3", "#854d0e", "#a16207"),
                "low": ("#f1f5f9", "#334155", "#475569"),
                "info": ("#e0f2fe", "#075985", "#0284c7"),
            }
            bg, text_color, border_color = sev_colors.get(sev, ("#f1f5f9", "#334155", "#475569"))
            
            diff_html = ""
            if f.get("remediation_diff"):
                diff_html = f"""
                <div class="diff-block">
                    <div class="diff-header">Suggested Code Remediation Diff</div>
                    <pre><code>{e(f["remediation_diff"])}</code></pre>
                </div>
                """

            line_str = f":{f['line']}" if f.get("line") else ""
            card = f"""
            <article class="finding-card sev-{sev}">
                <div class="finding-top">
                    <span class="sev-pill" style="background:{bg}; color:{text_color}; border:1px solid {border_color};">
                        {e(sev.upper())}
                    </span>
                    <span class="rule-id">{e(f["rule_id"])} &middot; ASVS {e(f["asvs_id"])}</span>
                    <h3 class="finding-title">{e(f["title"])}</h3>
                </div>
                <div class="finding-meta">
                    <strong>Location:</strong> <code>{e(f["location"])}{line_str}</code>
                </div>
                <div class="finding-evidence">
                    <strong>Evidence:</strong> {e(f["evidence"])}
                </div>
                <div class="finding-remediation">
                    <strong>Remediation:</strong> {e(f["remediation"])}
                </div>
                {diff_html}
            </article>
            """
            finding_cards.append(card)
        findings_html = "\n".join(finding_cards)
    else:
        findings_html = '<div class="clean-box">No critical code defects detected in the performed checks. Review the Verification Ledger below to confirm test boundaries.</div>'

    # Render ledger table rows
    ledger_rows = []
    for item in ledger:
        status = item["status"]
        if status == "verified_pass":
            status_badge = '<span class="status-badge status-pass">VERIFIED CLEAN</span>'
        elif status == "finding_fail":
            status_badge = '<span class="status-badge status-fail">FINDING DEFECT</span>'
        else:
            status_badge = '<span class="status-badge status-gap">UNVERIFIED GAP</span>'

        method = item["verification_method"].replace("_", " ").title()
        row = f"""
        <tr>
            <td class="font-mono"><strong>{e(item["asvs_id"])}</strong></td>
            <td><strong>{e(item["category"])}</strong></td>
            <td>{e(item["requirement"])}</td>
            <td>{status_badge}</td>
            <td><span class="method-tag">{e(method)}</span></td>
            <td class="ledger-reason">{e(item["evidence_or_reason"])}</td>
        </tr>
        """
        ledger_rows.append(row)
    ledger_html = "\n".join(ledger_rows)

    agency_name = report_data.get("agency_name") or os.environ.get("AGENCY_NAME")
    agency_email = report_data.get("agency_email") or os.environ.get("AGENCY_EMAIL") or "audits@productionready.dev"
    branding_title = f"{e(agency_name)} &middot; ProductionReady" if agency_name else "ProductionReady"

    reviewer = report_data.get("reviewer_sign_off", {})
    reviewer_section = f"""
    <section class="reviewer-card">
        <h2>Human Auditor Review & Verification Stamp</h2>
        <div class="reviewer-grid">
            <div><strong>Reviewer:</strong> {e(reviewer.get("reviewer_name") or "Unassigned / Automated Baseline")}</div>
            <div><strong>Auditor Email:</strong> {e(reviewer.get("reviewer_email") or agency_email)}</div>
            <div><strong>Date:</strong> {e(reviewer.get("review_date_utc") or report_data.get("scan_time_utc"))}</div>
            <div><strong>Status:</strong> <span class="badge-neutral">{e(reviewer.get("status", "pending").upper())}</span></div>
        </div>
        <div class="reviewer-notes">
            <strong>Auditor Notes:</strong> {e(reviewer.get("notes") or "Automated baseline inspection generated. For full manual sign-off and penetration check, submit for $299 reviewed delivery.")}
        </div>
    </section>
    """

    return f"""<!doctype html>
<html lang="en">
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>ProductionReady Assessment & Verification Report</title>
    <style>
        :root {{
            --bg: #0f172a;
            --card-bg: #1e293b;
            --text-main: #f8fafc;
            --text-muted: #94a3b8;
            --border: #334155;
            --accent: #38bdf8;
            --danger: #ef4444;
            --warning: #f59e0b;
            --success: #10b981;
        }}
        * {{ box-sizing: border-box; margin: 0; padding: 0; }}
        body {{
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
            background: #f8fafc;
            color: #0f172a;
            line-height: 1.6;
            padding: 40px 20px;
        }}
        .container {{
            max-width: 1040px;
            margin: 0 auto;
            background: #ffffff;
            border-radius: 14px;
            box-shadow: 0 4px 20px rgba(0,0,0,0.06);
            border: 1px solid #e2e8f0;
            overflow: hidden;
        }}
        header {{
            background: #0f172a;
            color: #ffffff;
            padding: 36px 40px;
            border-bottom: 3px solid #38bdf8;
        }}
        .header-top {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            flex-wrap: wrap;
            gap: 16px;
        }}
        .brand-title {{
            font-size: 26px;
            font-weight: 700;
            letter-spacing: -0.5px;
            display: flex;
            align-items: center;
            gap: 10px;
        }}
        .brand-tag {{
            font-size: 13px;
            background: #1e293b;
            color: #38bdf8;
            padding: 4px 10px;
            border-radius: 6px;
            font-weight: 600;
        }}
        .readiness-banner {{
            display: inline-block;
            background: {badge_bg};
            border: 1px solid {badge_border};
            color: #ffffff;
            padding: 6px 16px;
            border-radius: 999px;
            font-size: 13px;
            font-weight: 700;
            letter-spacing: 0.5px;
        }}
        .header-meta {{
            margin-top: 20px;
            font-size: 14px;
            color: #94a3b8;
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
            gap: 10px;
        }}
        .header-meta strong {{ color: #e2e8f0; }}
        main {{ padding: 36px 40px; }}
        .scorecard {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 16px;
            margin-bottom: 36px;
        }}
        .metric-card {{
            background: #f8fafc;
            border: 1px solid #e2e8f0;
            border-radius: 10px;
            padding: 20px;
            text-align: center;
        }}
        .metric-value {{
            font-size: 32px;
            font-weight: 800;
            line-height: 1.2;
            color: #0f172a;
        }}
        .metric-label {{
            font-size: 13px;
            font-weight: 600;
            text-transform: uppercase;
            color: #64748b;
            margin-top: 6px;
        }}
        .val-danger {{ color: #dc2626; }}
        .val-success {{ color: #059669; }}
        .val-warning {{ color: #d97706; }}
        h2 {{
            font-size: 20px;
            font-weight: 700;
            color: #0f172a;
            margin: 32px 0 16px;
            padding-bottom: 8px;
            border-bottom: 2px solid #f1f5f9;
            display: flex;
            align-items: center;
            justify-content: space-between;
        }}
        .finding-card {{
            border: 1px solid #e2e8f0;
            border-radius: 10px;
            padding: 20px 24px;
            margin-bottom: 18px;
            background: #ffffff;
            transition: box-shadow 0.2s;
        }}
        .finding-card:hover {{ box-shadow: 0 4px 12px rgba(0,0,0,0.05); }}
        .finding-card.sev-critical {{ border-left: 6px solid #dc2626; }}
        .finding-card.sev-high {{ border-left: 6px solid #ea580c; }}
        .finding-card.sev-medium {{ border-left: 6px solid #ca8a04; }}
        .finding-card.sev-low {{ border-left: 6px solid #64748b; }}
        .finding-card.sev-info {{ border-left: 6px solid #0284c7; }}
        .finding-top {{
            display: flex;
            align-items: center;
            gap: 12px;
            margin-bottom: 10px;
            flex-wrap: wrap;
        }}
        .sev-pill {{
            font-size: 11px;
            font-weight: 800;
            padding: 3px 8px;
            border-radius: 4px;
            letter-spacing: 0.5px;
        }}
        .rule-id {{
            font-size: 13px;
            font-family: monospace;
            color: #64748b;
        }}
        .finding-title {{
            font-size: 17px;
            font-weight: 700;
            color: #0f172a;
            flex-grow: 1;
        }}
        .finding-meta, .finding-evidence, .finding-remediation {{
            font-size: 14px;
            margin-top: 8px;
            color: #334155;
        }}
        .diff-block {{
            margin-top: 14px;
            background: #0f172a;
            border-radius: 8px;
            overflow: hidden;
        }}
        .diff-header {{
            background: #1e293b;
            color: #94a3b8;
            font-size: 12px;
            font-weight: 600;
            padding: 6px 14px;
            font-family: monospace;
        }}
        .diff-block pre {{
            margin: 0;
            padding: 12px 14px;
            color: #38bdf8;
            font-size: 13px;
            overflow-x: auto;
            font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;
        }}
        .clean-box {{
            background: #ecfdf5;
            border: 1px solid #a7f3d0;
            color: #065f46;
            padding: 20px;
            border-radius: 8px;
            font-weight: 500;
        }}
        table.ledger-table {{
            width: 100%;
            border-collapse: collapse;
            font-size: 13px;
            margin-top: 12px;
        }}
        table.ledger-table th {{
            background: #f1f5f9;
            text-align: left;
            padding: 10px 12px;
            font-weight: 700;
            color: #334155;
            border-bottom: 2px solid #cbd5e1;
        }}
        table.ledger-table td {{
            padding: 10px 12px;
            border-bottom: 1px solid #e2e8f0;
            vertical-align: top;
        }}
        .status-badge {{
            display: inline-block;
            font-size: 11px;
            font-weight: 700;
            padding: 2px 8px;
            border-radius: 999px;
            white-space: nowrap;
        }}
        .status-pass {{ background: #dcfce7; color: #15803d; border: 1px solid #86efac; }}
        .status-fail {{ background: #fee2e2; color: #b91c1c; border: 1px solid #fca5a5; }}
        .status-gap {{ background: #fef3c7; color: #b45309; border: 1px solid #fde68a; }}
        .method-tag {{
            font-size: 11px;
            font-weight: 600;
            background: #f1f5f9;
            padding: 2px 6px;
            border-radius: 4px;
            color: #475569;
            white-space: nowrap;
        }}
        .font-mono {{ font-family: monospace; }}
        .ledger-reason {{ color: #475569; }}
        .reviewer-card {{
            background: #f8fafc;
            border: 1px solid #cbd5e1;
            border-radius: 10px;
            padding: 24px;
            margin-top: 36px;
        }}
        .reviewer-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 12px;
            font-size: 14px;
            margin: 14px 0;
        }}
        .badge-neutral {{
            background: #e2e8f0;
            padding: 2px 8px;
            border-radius: 4px;
            font-weight: 700;
            font-size: 12px;
        }}
        .reviewer-notes {{
            background: #ffffff;
            border: 1px solid #e2e8f0;
            padding: 12px;
            border-radius: 6px;
            font-size: 14px;
            color: #334155;
        }}
        footer {{
            padding: 24px 40px;
            background: #f1f5f9;
            border-top: 1px solid #e2e8f0;
            font-size: 12px;
            color: #64748b;
        }}
        code {{
            background: #f1f5f9;
            padding: 2px 5px;
            border-radius: 4px;
            font-family: monospace;
            font-size: 13px;
        }}
    </style>
</head>
<body>
    <div class="container">
        <header>
            <div class="header-top">
                <div class="brand-title">
                    {branding_title}
                    <span class="brand-tag">v{e(report_data.get("version", "0.2.0"))}</span>
                </div>
                <div class="readiness-banner">{e(readiness)}</div>
            </div>
            <div class="header-meta">
                <div><strong>Target:</strong> <code>{e(report_data.get("target"))}</code></div>
                <div><strong>Intake Type:</strong> {e(report_data.get("target_type"))}</div>
                <div><strong>Scan Date (UTC):</strong> {e(report_data.get("scan_time_utc"))}</div>
                <div><strong>Commit SHA:</strong> <code>{e(report_data.get("commit_sha") or "Local Working Tree")}</code></div>
            </div>
        </header>

        <main>
            <section class="scorecard">
                <div class="metric-card">
                    <div class="metric-value val-danger">{blockers}</div>
                    <div class="metric-label">Launch Blockers (Crit/High)</div>
                </div>
                <div class="metric-card">
                    <div class="metric-value">{len(findings)}</div>
                    <div class="metric-label">Total Code Findings</div>
                </div>
                <div class="metric-card">
                    <div class="metric-value val-success">{verified_count}</div>
                    <div class="metric-label">ASVS Controls Verified Clean</div>
                </div>
                <div class="metric-card">
                    <div class="metric-value val-warning">{gap_count}</div>
                    <div class="metric-label">Unverified Surface Gaps</div>
                </div>
            </section>

            <h2>Findings ({len(findings)})</h2>
            <div class="findings-list">
                {findings_html}
            </div>

            <h2>Checks performed</h2>
            <ul style="font-size:14px; color:#334155; margin: 12px 0 24px 20px;">
                {"".join(f"<li>{e(c)}</li>" for c in report_data.get("coverage", {}).get("checks_performed", []))}
            </ul>

            <h2>OWASP ASVS 5.0 Verification & Gap Ledger ({len(ledger)})</h2>
            <p style="font-size:14px; color:#64748b; margin-bottom:12px;">
                Non-negotiable audit standard: Separates controls actively verified from defects and unverified operational surfaces.
            </p>
            <div style="overflow-x: auto;">
                <table class="ledger-table">
                    <thead>
                        <tr>
                            <th>ASVS</th>
                            <th>Category</th>
                            <th>Standard Requirement</th>
                            <th>Status</th>
                            <th>Method</th>
                            <th>Evidence / Reason</th>
                        </tr>
                    </thead>
                    <tbody>
                        {ledger_html}
                    </tbody>
                </table>
            </div>

            {reviewer_section}
        </main>

        <footer>
            <strong>Non-Warranty & Verification Disclaimer:</strong>
            {e(report_data.get("disclaimer"))}
        </footer>
    </div>
</body>
</html>
"""
