"""Initial database schema migration for ProductionReady orchestrator.

Revision ID: 0001_initial_schema
Revises: 
Create Date: 2026-11-12 14:30:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = "0001_initial_schema"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "projects",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("repository_url", sa.String(), nullable=False),
        sa.Column("default_branch", sa.String(), server_default="main", nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "assessments",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("project_id", sa.String(), nullable=False),
        sa.Column("commit_sha", sa.String(), nullable=True),
        sa.Column("target_type", sa.String(), server_default="local_directory", nullable=False),
        sa.Column("status", sa.String(), server_default="queued", nullable=False),
        sa.Column("readiness_status", sa.String(), server_default="UNVERIFIED", nullable=False),
        sa.Column("blockers_count", sa.Integer(), server_default="0", nullable=False),
        sa.Column("total_findings_count", sa.Integer(), server_default="0", nullable=False),
        sa.Column("verified_controls_count", sa.Integer(), server_default="0", nullable=False),
        sa.Column("unverified_gaps_count", sa.Integer(), server_default="0", nullable=False),
        sa.Column("reviewer_name", sa.String(), nullable=True),
        sa.Column("reviewer_status", sa.String(), server_default="pending", nullable=False),
        sa.Column("reviewer_notes", sa.Text(), nullable=True),
        sa.Column("html_report_path", sa.String(), nullable=True),
        sa.Column("json_report_path", sa.String(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["project_id"], ["projects.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "findings",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("assessment_id", sa.String(), nullable=False),
        sa.Column("rule_id", sa.String(), nullable=False),
        sa.Column("asvs_id", sa.String(), nullable=False),
        sa.Column("severity", sa.String(), nullable=False),
        sa.Column("title", sa.String(), nullable=False),
        sa.Column("location", sa.String(), nullable=False),
        sa.Column("line", sa.Integer(), nullable=True),
        sa.Column("evidence", sa.Text(), nullable=False),
        sa.Column("remediation", sa.Text(), nullable=False),
        sa.Column("remediation_diff", sa.Text(), nullable=True),
        sa.Column("status", sa.String(), server_default="OPEN", nullable=False),
        sa.Column("resolution_notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["assessment_id"], ["assessments.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "verification_items",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("assessment_id", sa.String(), nullable=False),
        sa.Column("asvs_id", sa.String(), nullable=False),
        sa.Column("category", sa.String(), nullable=False),
        sa.Column("requirement", sa.Text(), nullable=False),
        sa.Column("status", sa.String(), nullable=False),
        sa.Column("verification_method", sa.String(), nullable=False),
        sa.Column("evidence_or_reason", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["assessment_id"], ["assessments.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "audit_events",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("assessment_id", sa.String(), nullable=False),
        sa.Column("event_type", sa.String(), nullable=False),
        sa.Column("actor", sa.String(), nullable=False),
        sa.Column("payload_json", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["assessment_id"], ["assessments.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )


def downgrade() -> None:
    op.drop_table("audit_events")
    op.drop_table("verification_items")
    op.drop_table("findings")
    op.drop_table("assessments")
    op.drop_table("projects")
