/** API Client for ProductionReady FastAPI orchestrator. */

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
const API_KEY = process.env.NEXT_PUBLIC_API_KEY || "pr_live_dev_test_key_0000";

function getHeaders(contentType = "application/json"): HeadersInit {
  const headers: Record<string, string> = {
    "X-API-Key": API_KEY,
  };
  if (contentType) {
    headers["Content-Type"] = contentType;
  }
  return headers;
}

export interface Project {
  id: string;
  name: string;
  repository_url: string;
  default_branch: string;
  created_at: string;
  updated_at: string;
  latest_assessment_status?: string | null;
  latest_readiness_status?: string | null;
}

export interface Finding {
  id: string;
  assessment_id: string;
  rule_id: string;
  asvs_id: string;
  severity: "critical" | "high" | "medium" | "low" | "info";
  title: string;
  location: string;
  line: number | null;
  evidence: string;
  remediation: string;
  remediation_diff?: string | null;
  status: "OPEN" | "RESOLVED" | "ACCEPTED_RISK";
  resolution_notes?: string | null;
}

export interface VerificationItem {
  id: string;
  assessment_id: string;
  asvs_id: string;
  category: string;
  requirement: string;
  status: "verified_pass" | "finding_fail" | "unverified_gap";
  verification_method: string;
  evidence_or_reason: string;
}

export interface AssessmentDetail {
  id: string;
  project_id: string;
  commit_sha?: string | null;
  target_type: string;
  status: string;
  readiness_status: string;
  blockers_count: number;
  total_findings_count: number;
  verified_controls_count: number;
  unverified_gaps_count: number;
  reviewer_name?: string | null;
  reviewer_status: string;
  reviewer_notes?: string | null;
  created_at: string;
  completed_at?: string | null;
  findings: Finding[];
  verification_items: VerificationItem[];
}

export async function fetchProjects(): Promise<Project[]> {
  const res = await fetch(`${API_BASE}/api/projects`, {
    cache: "no-store",
    headers: getHeaders(""),
  });
  if (!res.ok) throw new Error("Failed to load projects");
  return res.json();
}

export async function createProject(data: { name: string; repository_url: string; default_branch: string }): Promise<Project> {
  const res = await fetch(`${API_BASE}/api/projects`, {
    method: "POST",
    headers: getHeaders("application/json"),
    body: JSON.stringify(data),
  });
  if (!res.ok) throw new Error("Failed to register project");
  return res.json();
}

export async function triggerAssessment(projectId: string, ref = "main"): Promise<{ id: string }> {
  const res = await fetch(`${API_BASE}/api/projects/${projectId}/assessments?sync=true`, {
    method: "POST",
    headers: getHeaders("application/json"),
    body: JSON.stringify({ ref }),
  });
  if (!res.ok) throw new Error("Failed to trigger assessment");
  return res.json();
}

export async function fetchAssessment(assessmentId: string): Promise<AssessmentDetail> {
  const res = await fetch(`${API_BASE}/api/assessments/${assessmentId}`, {
    cache: "no-store",
    headers: getHeaders(""),
  });
  if (!res.ok) throw new Error("Failed to fetch assessment");
  return res.json();
}

export async function updateFindingStatus(findingId: string, status: string, notes?: string): Promise<Finding> {
  const res = await fetch(`${API_BASE}/api/findings/${findingId}/status`, {
    method: "PATCH",
    headers: getHeaders("application/json"),
    body: JSON.stringify({ status, resolution_notes: notes }),
  });
  if (!res.ok) throw new Error("Failed to update finding status");
  return res.json();
}

export async function requestReassessment(assessmentId: string): Promise<{ id: string }> {
  const res = await fetch(`${API_BASE}/api/assessments/${assessmentId}/reassessment`, {
    method: "POST",
    headers: getHeaders("application/json"),
  });
  if (!res.ok) throw new Error("Failed to request reassessment");
  return res.json();
}

export async function submitReviewerSignoff(
  assessmentId: string,
  reviewerName: string,
  reviewerStatus: string,
  reviewerNotes?: string
): Promise<any> {
  const res = await fetch(`${API_BASE}/api/assessments/${assessmentId}/review`, {
    method: "POST",
    headers: getHeaders("application/json"),
    body: JSON.stringify({
      reviewer_name: reviewerName,
      reviewer_status: reviewerStatus,
      reviewer_notes: reviewerNotes,
    }),
  });
  if (!res.ok) throw new Error("Failed to apply reviewer sign-off");
  return res.json();
}
