"use client";
import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import Link from "next/link";
import { AssessmentDetail, Finding, fetchAssessment, requestReassessment } from "@/lib/api";
import FindingCard from "@/components/FindingCard";

export default function RemediationPage() {
  const params = useParams();
  const id = params?.id as string;

  const [assessment, setAssessment] = useState<AssessmentDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [reassessing, setReassessing] = useState(false);
  const [statusFilter, setStatusFilter] = useState<string>("ALL");
  const [sevFilter, setSevFilter] = useState<string>("ALL");

  const load = async () => {
    try {
      const data = await fetchAssessment(id);
      setAssessment(data);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (id) load();
  }, [id]);

  const handleStatusChange = (updated: Finding) => {
    if (!assessment) return;
    const nextFindings = assessment.findings.map((f) => (f.id === updated.id ? updated : f));
    setAssessment({ ...assessment, findings: nextFindings });
  };

  const handleRequestReassessment = async () => {
    if (!confirm("This will trigger a clean verification pass against the repository. Proceed?")) return;
    setReassessing(true);
    try {
      const res = await requestReassessment(id);
      window.location.href = `/assessments/${res.id}`;
    } catch (err) {
      alert("Failed to initiate reassessment");
    } finally {
      setReassessing(false);
    }
  };

  if (loading) {
    return <div className="p-12 text-center text-slate-500 text-sm">Loading remediation items...</div>;
  }

  if (!assessment) {
    return <div className="p-12 text-center text-red-500 text-sm">Assessment not found.</div>;
  }

  const findings = assessment.findings || [];
  const openBlockers = findings.filter(
    (f) => f.status === "OPEN" && (f.severity === "critical" || f.severity === "high")
  ).length;

  const filtered = findings.filter((f) => {
    if (statusFilter !== "ALL" && f.status !== statusFilter) return false;
    if (sevFilter !== "ALL" && f.severity !== sevFilter.toLowerCase()) return false;
    return true;
  });

  return (
    <div className="space-y-8">
      {/* Header */}
      <div className="flex flex-wrap items-center justify-between gap-4 pb-4 border-b border-slate-200">
        <div>
          <div className="flex items-center gap-3">
            <Link href={`/assessments/${assessment.id}`} className="text-xs text-sky-600 font-semibold hover:underline">
              &larr; Back to Assessment Report
            </Link>
            <span className="text-slate-300">/</span>
            <span className="text-xs font-mono text-slate-500">Remediation Workspace</span>
          </div>
          <h1 className="text-2xl font-black text-slate-900 mt-1">
            Remediation Action Plan
          </h1>
          <p className="text-xs text-slate-500 mt-1">
            Review actionable code diffs, mark resolved issues, or accept justified risks before re-scanning.
          </p>
        </div>

        <div className="flex items-center gap-3">
          <button
            disabled={reassessing}
            onClick={handleRequestReassessment}
            className="px-5 py-2.5 bg-slate-900 hover:bg-slate-800 text-white font-bold rounded-xl text-xs transition-colors shadow-sm disabled:opacity-50 flex items-center gap-2"
          >
            {reassessing ? (
              "Running Reassessment..."
            ) : (
              <>
                <span>Request Reassessment</span>
                <span className="w-2 h-2 rounded-full bg-emerald-400"></span>
              </>
            )}
          </button>
        </div>
      </div>

      {/* Blocker Alert Banner */}
      <div
        className={`p-4 rounded-xl border flex items-center justify-between gap-4 text-xs ${
          openBlockers > 0
            ? "bg-red-50 text-red-900 border-red-200"
            : "bg-emerald-50 text-emerald-900 border-emerald-200"
        }`}
      >
        <div className="font-semibold">
          {openBlockers > 0
            ? `${openBlockers} active launch blocker(s) remaining. Fix or accept risks before deployment.`
            : "All critical and high severity blockers have been resolved! Ready to request reassessment."}
        </div>
        <div className="font-mono text-[11px] text-slate-500">
          {findings.filter((f) => f.status === "RESOLVED").length} of {findings.length} Resolved
        </div>
      </div>

      {/* Filter Toolbar */}
      <div className="flex flex-wrap items-center justify-between gap-4 bg-white p-4 border border-slate-200 rounded-xl shadow-sm text-xs">
        <div className="flex items-center gap-2">
          <span className="font-semibold text-slate-500">Status:</span>
          {["ALL", "OPEN", "RESOLVED", "ACCEPTED_RISK"].map((st) => (
            <button
              key={st}
              onClick={() => setStatusFilter(st)}
              className={`px-2.5 py-1 rounded-lg border font-semibold transition-colors ${
                statusFilter === st
                  ? "bg-slate-900 text-white border-slate-900"
                  : "bg-slate-50 text-slate-600 border-slate-200 hover:bg-slate-100"
              }`}
            >
              {st}
            </button>
          ))}
        </div>

        <div className="flex items-center gap-2">
          <span className="font-semibold text-slate-500">Severity:</span>
          {["ALL", "CRITICAL", "HIGH", "MEDIUM", "LOW"].map((sv) => (
            <button
              key={sv}
              onClick={() => setSevFilter(sv)}
              className={`px-2.5 py-1 rounded-lg border font-semibold transition-colors ${
                sevFilter === sv
                  ? "bg-slate-900 text-white border-slate-900"
                  : "bg-slate-50 text-slate-600 border-slate-200 hover:bg-slate-100"
              }`}
            >
              {sv}
            </button>
          ))}
        </div>
      </div>

      {/* Findings List */}
      <div className="space-y-4">
        {filtered.length === 0 ? (
          <div className="p-12 text-center bg-white border border-slate-200 rounded-xl text-slate-400 text-sm">
            No findings match the current filter criteria.
          </div>
        ) : (
          filtered.map((f) => (
            <FindingCard key={f.id} finding={f} onStatusChange={handleStatusChange} />
          ))
        )}
      </div>
    </div>
  );
}
