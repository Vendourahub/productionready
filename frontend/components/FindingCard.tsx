"use client";
import { useState } from "react";
import { Finding, updateFindingStatus } from "@/lib/api";

export default function FindingCard({
  finding,
  onStatusChange,
}: {
  finding: Finding;
  onStatusChange?: (updated: Finding) => void;
}) {
  const [loading, setLoading] = useState(false);
  const [copied, setCopied] = useState(false);

  const handleStatus = async (newStatus: "OPEN" | "RESOLVED" | "ACCEPTED_RISK") => {
    setLoading(true);
    try {
      const updated = await updateFindingStatus(finding.id, newStatus);
      if (onStatusChange) onStatusChange(updated);
    } catch (e) {
      alert("Failed to update status");
    } finally {
      setLoading(false);
    }
  };

  const copyDiff = () => {
    if (finding.remediation_diff) {
      navigator.clipboard.writeText(finding.remediation_diff);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    }
  };

  const getBorderColor = (sev: string) => {
    switch (sev) {
      case "critical":
        return "border-l-red-600";
      case "high":
        return "border-l-orange-500";
      case "medium":
        return "border-l-amber-500";
      case "low":
        return "border-l-slate-400";
      default:
        return "border-l-sky-500";
    }
  };

  const getPillColor = (sev: string) => {
    switch (sev) {
      case "critical":
        return "bg-red-50 text-red-700 border-red-200";
      case "high":
        return "bg-orange-50 text-orange-700 border-orange-200";
      case "medium":
        return "bg-amber-50 text-amber-700 border-amber-200";
      case "low":
        return "bg-slate-100 text-slate-700 border-slate-200";
      default:
        return "bg-sky-50 text-sky-700 border-sky-200";
    }
  };

  return (
    <article
      className={`bg-white border border-slate-200 rounded-xl p-5 shadow-sm border-l-4 ${getBorderColor(
        finding.severity
      )}`}
    >
      <div className="flex flex-wrap items-center justify-between gap-3 mb-3">
        <div className="flex items-center gap-2">
          <span
            className={`px-2.5 py-0.5 rounded text-[11px] font-bold uppercase tracking-wider border ${getPillColor(
              finding.severity
            )}`}
          >
            {finding.severity}
          </span>
          <span className="font-mono text-xs text-slate-500">
            {finding.rule_id} &middot; ASVS {finding.asvs_id}
          </span>
        </div>

        <div className="flex items-center gap-2">
          <span
            className={`px-2 py-0.5 rounded-full text-[11px] font-bold ${
              finding.status === "RESOLVED"
                ? "bg-emerald-50 text-emerald-700 border border-emerald-200"
                : finding.status === "ACCEPTED_RISK"
                ? "bg-slate-100 text-slate-700 border border-slate-200"
                : "bg-red-50 text-red-700 border border-red-200"
            }`}
          >
            {finding.status}
          </span>
        </div>
      </div>

      <h3 className="text-base font-bold text-slate-900 mb-2">{finding.title}</h3>

      <div className="text-xs text-slate-600 mb-2">
        <strong>Location:</strong>{" "}
        <code className="bg-slate-100 px-1.5 py-0.5 rounded text-slate-800 font-mono">
          {finding.location}
          {finding.line ? `:${finding.line}` : ""}
        </code>
      </div>

      <div className="text-xs text-slate-600 mb-2">
        <strong>Evidence:</strong> {finding.evidence}
      </div>

      <div className="text-xs text-slate-600 mb-3">
        <strong>Remediation:</strong> {finding.remediation}
      </div>

      {finding.remediation_diff && (
        <div className="mt-3 bg-slate-900 rounded-lg overflow-hidden border border-slate-800">
          <div className="flex items-center justify-between px-3 py-1.5 bg-slate-800/80 text-[11px] text-slate-300 font-mono">
            <span>Suggested Fix Diff</span>
            <button
              onClick={copyDiff}
              className="text-sky-400 hover:text-sky-300 transition-colors"
            >
              {copied ? "Copied!" : "Copy Diff"}
            </button>
          </div>
          <pre className="p-3 text-xs text-sky-300 overflow-x-auto font-mono">
            <code>{finding.remediation_diff}</code>
          </pre>
        </div>
      )}

      <div className="mt-4 pt-3 border-t border-slate-100 flex items-center justify-end gap-2 text-xs">
        {finding.status !== "RESOLVED" && (
          <button
            disabled={loading}
            onClick={() => handleStatus("RESOLVED")}
            className="px-3 py-1 bg-emerald-600 hover:bg-emerald-700 text-white font-medium rounded-lg transition-colors"
          >
            Mark Resolved
          </button>
        )}
        {finding.status !== "ACCEPTED_RISK" && (
          <button
            disabled={loading}
            onClick={() => handleStatus("ACCEPTED_RISK")}
            className="px-3 py-1 bg-slate-100 hover:bg-slate-200 text-slate-700 font-medium rounded-lg transition-colors border border-slate-300"
          >
            Accept Risk
          </button>
        )}
        {finding.status !== "OPEN" && (
          <button
            disabled={loading}
            onClick={() => handleStatus("OPEN")}
            className="px-3 py-1 bg-slate-50 hover:bg-slate-100 text-slate-600 font-medium rounded-lg transition-colors border border-slate-200"
          >
            Reopen
          </button>
        )}
      </div>
    </article>
  );
}
