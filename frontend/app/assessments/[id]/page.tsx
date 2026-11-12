"use client";
import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import Link from "next/link";
import { AssessmentDetail, fetchAssessment, submitReviewerSignoff } from "@/lib/api";
import Scorecard from "@/components/Scorecard";
import VerificationLedger from "@/components/VerificationLedger";

export default function AssessmentDetailPage() {
  const params = useParams();
  const id = params?.id as string;

  const [assessment, setAssessment] = useState<AssessmentDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [showSignoff, setShowSignoff] = useState(false);
  const [reviewerName, setReviewerName] = useState("");
  const [reviewerStatus, setReviewerStatus] = useState("approved");
  const [reviewerNotes, setReviewerNotes] = useState("");
  const [savingSignoff, setSavingSignoff] = useState(false);

  const load = async () => {
    try {
      const data = await fetchAssessment(id);
      setAssessment(data);
      if (data.reviewer_name) setReviewerName(data.reviewer_name);
      if (data.reviewer_status) setReviewerStatus(data.reviewer_status);
      if (data.reviewer_notes) setReviewerNotes(data.reviewer_notes);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (id) load();
  }, [id]);

  const handleSignoff = async (e: React.FormEvent) => {
    e.preventDefault();
    setSavingSignoff(true);
    try {
      await submitReviewerSignoff(id, reviewerName, reviewerStatus, reviewerNotes);
      setShowSignoff(false);
      await load();
    } catch (err) {
      alert("Failed to submit auditor signoff");
    } finally {
      setSavingSignoff(false);
    }
  };

  if (loading) {
    return <div className="p-12 text-center text-slate-500 text-sm">Loading assessment evidence...</div>;
  }

  if (!assessment) {
    return <div className="p-12 text-center text-red-500 text-sm">Assessment not found.</div>;
  }

  const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

  return (
    <div className="space-y-8">
      {/* Header & Quick Actions */}
      <div className="flex flex-wrap items-center justify-between gap-4 pb-4 border-b border-slate-200">
        <div>
          <div className="flex items-center gap-3">
            <Link href="/" className="text-xs text-sky-600 font-semibold hover:underline">
              &larr; Back to Projects
            </Link>
            <span className="text-slate-300">/</span>
            <span className="text-xs font-mono text-slate-500">Assessment {assessment.id.slice(0, 8)}</span>
          </div>
          <h1 className="text-2xl font-black text-slate-900 mt-1">
            Deployment Readiness Assessment
          </h1>
          <div className="text-xs text-slate-500 mt-1 space-x-3">
            <span>Commit: <code className="font-mono bg-slate-100 px-1 py-0.5 rounded">{assessment.commit_sha || "Local Tree"}</code></span>
            <span>&middot;</span>
            <span>Intake: {assessment.target_type}</span>
            <span>&middot;</span>
            <span>Audited: {new Date(assessment.created_at).toUTCString()}</span>
          </div>
        </div>

        <div className="flex flex-wrap items-center gap-2">
          <Link
            href={`/remediation/${assessment.id}`}
            className="px-4 py-2 bg-sky-600 hover:bg-sky-500 text-white font-bold rounded-xl text-xs transition-colors shadow-sm"
          >
            Remediation Workspace ({assessment.total_findings_count}) &rarr;
          </Link>
          <a
            href={`${API_BASE}/api/assessments/${assessment.id}/report.html`}
            target="_blank"
            rel="noreferrer"
            className="px-4 py-2 bg-white hover:bg-slate-50 text-slate-700 font-semibold rounded-xl text-xs transition-colors border border-slate-300 shadow-sm"
          >
            View Executive HTML
          </a>
          <a
            href={`${API_BASE}/api/assessments/${assessment.id}/report.json`}
            target="_blank"
            rel="noreferrer"
            className="px-4 py-2 bg-white hover:bg-slate-50 text-slate-700 font-semibold rounded-xl text-xs transition-colors border border-slate-300 shadow-sm"
          >
            Export JSON
          </a>
        </div>
      </div>

      {/* Scorecard */}
      <Scorecard
        readinessStatus={assessment.readiness_status}
        blockersCount={assessment.blockers_count}
        totalFindingsCount={assessment.total_findings_count}
        verifiedControlsCount={assessment.verified_controls_count}
        unverifiedGapsCount={assessment.unverified_gaps_count}
      />

      {/* Human Auditor Verification Card ($299 Package Stamp) */}
      <div className="bg-slate-900 text-white rounded-xl p-6 border border-slate-800 shadow-sm">
        <div className="flex flex-wrap items-center justify-between gap-4 mb-4">
          <div>
            <span className="text-[10px] font-bold tracking-widest text-sky-400 uppercase bg-slate-800 px-2.5 py-0.5 rounded border border-slate-700">
              $299 Commercial Deliverable
            </span>
            <h3 className="text-base font-bold mt-1">Human Auditor Verification Stamp</h3>
          </div>
          <button
            onClick={() => setShowSignoff(true)}
            className="px-3 py-1 bg-slate-800 hover:bg-slate-700 text-sky-400 border border-slate-700 font-semibold rounded-lg text-xs transition-colors"
          >
            {assessment.reviewer_name ? "Edit Auditor Stamp" : "+ Sign Assessment"}
          </button>
        </div>

        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-xs">
          <div>
            <div className="text-slate-400">Auditor:</div>
            <div className="font-semibold text-slate-200 mt-0.5">
              {assessment.reviewer_name || "Unassigned"}
            </div>
          </div>
          <div>
            <div className="text-slate-400">Review Status:</div>
            <div className="mt-0.5">
              <span className={`px-2 py-0.5 rounded font-bold uppercase text-[10px] ${
                assessment.reviewer_status === "approved"
                  ? "bg-emerald-950 text-emerald-400 border border-emerald-800"
                  : "bg-amber-950 text-amber-400 border border-amber-800"
              }`}>
                {assessment.reviewer_status}
              </span>
            </div>
          </div>
          <div className="col-span-2">
            <div className="text-slate-400">Auditor Notes for Client:</div>
            <div className="text-slate-300 mt-0.5 italic">
              {assessment.reviewer_notes || "No custom auditor notes attached."}
            </div>
          </div>
        </div>
      </div>

      {/* ASVS 5.0 Verification & Gap Ledger */}
      <VerificationLedger items={assessment.verification_items} />

      {/* Sign-off Modal */}
      {showSignoff && (
        <div className="fixed inset-0 bg-slate-900/60 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <div className="bg-white rounded-2xl max-w-md w-full p-6 shadow-2xl border border-slate-200">
            <h3 className="text-base font-bold text-slate-900 mb-1">Auditor Sign-off</h3>
            <p className="text-xs text-slate-500 mb-4">
              Add your auditor stamp and launch recommendations to the customer-facing report.
            </p>

            <form onSubmit={handleSignoff} className="space-y-4 text-xs">
              <div>
                <label className="block font-semibold text-slate-700 mb-1">Auditor Name & Credentials</label>
                <input
                  type="text"
                  required
                  placeholder="e.g. Jane Doe, Senior AppSec Auditor"
                  value={reviewerName}
                  onChange={(e) => setReviewerName(e.target.value)}
                  className="w-full px-3 py-2 border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-sky-500"
                />
              </div>

              <div>
                <label className="block font-semibold text-slate-700 mb-1">Audit Status</label>
                <select
                  value={reviewerStatus}
                  onChange={(e) => setReviewerStatus(e.target.value)}
                  className="w-full px-3 py-2 border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-sky-500"
                >
                  <option value="approved">Approved for Production</option>
                  <option value="changes_requested">Changes Requested (Blockers Active)</option>
                  <option value="pending">Pending Further Audit</option>
                </select>
              </div>

              <div>
                <label className="block font-semibold text-slate-700 mb-1">Auditor Notes</label>
                <textarea
                  rows={3}
                  placeholder="Manual verification notes regarding RLS, webhooks, and deployment safety..."
                  value={reviewerNotes}
                  onChange={(e) => setReviewerNotes(e.target.value)}
                  className="w-full px-3 py-2 border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-sky-500"
                />
              </div>

              <div className="flex justify-end gap-2 pt-3 border-t border-slate-100">
                <button
                  type="button"
                  onClick={() => setShowSignoff(false)}
                  className="px-4 py-2 bg-slate-100 hover:bg-slate-200 text-slate-700 font-semibold rounded-lg transition-colors"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={savingSignoff}
                  className="px-4 py-2 bg-sky-600 hover:bg-sky-500 text-white font-semibold rounded-lg transition-colors disabled:opacity-50"
                >
                  {savingSignoff ? "Saving..." : "Apply Stamp"}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
