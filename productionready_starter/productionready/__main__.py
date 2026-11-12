"""Command-line entry point for ProductionReady assessment engine."""
from __future__ import annotations
import argparse
import json
import sys
from pathlib import Path

from .scanner import scan, render_html
from .intake import intake_repository


def main():
    parser = argparse.ArgumentParser(
        description="ProductionReady v0.2 — Evidence-backed security verification and remediation engine."
    )
    parser.add_argument(
        "target",
        help="Local repository directory or GitHub repository URL (e.g. 'owner/repo' or 'https://github.com/owner/repo')",
    )
    parser.add_argument(
        "--output",
        default="productionready-assessment",
        help="Output report prefix (creates <prefix>.json and <prefix>.html)",
    )
    parser.add_argument(
        "--github-token",
        default=None,
        help="GitHub personal access token for private repositories",
    )
    parser.add_argument(
        "--ref",
        default=None,
        help="Branch or commit SHA to inspect for remote GitHub repositories",
    )
    parser.add_argument(
        "--reviewer",
        default=None,
        help="Auditor name for the human verification stamp ($299 audit package)",
    )
    parser.add_argument(
        "--notes",
        default=None,
        help="Auditor evaluation notes to include in the client report",
    )

    args = parser.parse_args()

    try:
        with intake_repository(args.target, github_token=args.github_token, ref=args.ref) as (repo_path, intake_type, commit_sha):
            report = scan(
                root=repo_path,
                target_type=intake_type,
                commit_sha=commit_sha,
                reviewer_name=args.reviewer,
                reviewer_notes=args.notes,
            )
            # Retain original target name in report for clarity
            report["target"] = args.target

            out = Path(args.output)
            json_file = out.with_suffix(".json")
            html_file = out.with_suffix(".html")

            json_file.write_text(json.dumps(report, indent=2), encoding="utf-8")
            html_file.write_text(render_html(report), encoding="utf-8")

            readiness = report["readiness_status"]
            blockers = report["summary"]["by_severity"]["critical"] + report["summary"]["by_severity"]["high"]
            verified = report["summary"]["verified_controls"]
            gaps = report["summary"]["unverified_gaps"]

            print("=" * 64)
            print(f"ProductionReady Assessment Complete -- {readiness}")
            print("=" * 64)
            print(f"Target:               {args.target} ({intake_type})")
            print(f"Files Inspected:      {report['coverage_summary']['files_inspected']}")
            print(f"Launch Blockers:      {blockers} (Critical/High defects)")
            print(f"Total Findings:       {report['summary']['total']}")
            print(f"Verified ASVS Clean:  {verified} controls")
            print(f"Unverified Gaps:      {gaps} controls requiring external/dynamic test")
            print(f"Reports Generated:    {json_file.resolve()} | {html_file.resolve()}")
            print("=" * 64)

            # Return exit code 1 if critical or high blockers exist, 0 otherwise
            if blockers > 0:
                sys.exit(1)

    except Exception as e:
        print(f"Error during ProductionReady assessment: {e}", file=sys.stderr)
        sys.exit(2)


if __name__ == "__main__":
    main()
