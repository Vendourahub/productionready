"use client";
import { useState } from "react";
import { VerificationItem } from "@/lib/api";

export default function VerificationLedger({ items }: { items: VerificationItem[] }) {
  const [filter, setFilter] = useState<string>("all");

  const filtered = items.filter((item) => {
    if (filter === "all") return true;
    return item.status === filter;
  });

  return (
    <div className="bg-white border border-slate-200 rounded-xl shadow-sm overflow-hidden">
      <div className="p-5 border-b border-slate-200 flex flex-wrap items-center justify-between gap-4">
        <div>
          <h2 className="text-lg font-bold text-slate-900">
            OWASP ASVS 5.0 Verification & Gap Ledger
          </h2>
          <p className="text-xs text-slate-500 mt-0.5">
            Non-negotiable architectural standard: Separates controls verified from defects and unverified operational surfaces.
          </p>
        </div>

        <div className="flex gap-2">
          {["all", "verified_pass", "finding_fail", "unverified_gap"].map((f) => (
            <button
              key={f}
              onClick={() => setFilter(f)}
              className={`px-3 py-1 text-xs font-semibold rounded-lg border transition-colors ${
                filter === f
                  ? "bg-slate-900 text-white border-slate-900"
                  : "bg-slate-50 text-slate-600 border-slate-200 hover:bg-slate-100"
              }`}
            >
              {f === "all"
                ? "All Controls"
                : f === "verified_pass"
                ? "Verified Clean"
                : f === "finding_fail"
                ? "Findings"
                : "Unverified Gaps"}
            </button>
          ))}
        </div>
      </div>

      <div className="overflow-x-auto">
        <table className="w-full text-left text-xs border-collapse">
          <thead>
            <tr className="bg-slate-50 border-b border-slate-200 text-slate-600 font-bold uppercase tracking-wider">
              <th className="py-3 px-4">ASVS</th>
              <th className="py-3 px-4">Category</th>
              <th className="py-3 px-4">Standard Requirement</th>
              <th className="py-3 px-4">Status</th>
              <th className="py-3 px-4">Method</th>
              <th className="py-3 px-4">Evidence / Reason</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-100">
            {filtered.map((item) => {
              let badge = null;
              if (item.status === "verified_pass") {
                badge = (
                  <span className="inline-block px-2 py-0.5 rounded-full font-bold text-[10px] bg-emerald-50 text-emerald-700 border border-emerald-200">
                    VERIFIED CLEAN
                  </span>
                );
              } else if (item.status === "finding_fail") {
                badge = (
                  <span className="inline-block px-2 py-0.5 rounded-full font-bold text-[10px] bg-red-50 text-red-700 border border-red-200">
                    FINDING DEFECT
                  </span>
                );
              } else {
                badge = (
                  <span className="inline-block px-2 py-0.5 rounded-full font-bold text-[10px] bg-amber-50 text-amber-700 border border-amber-200">
                    UNVERIFIED GAP
                  </span>
                );
              }

              return (
                <tr key={item.id} className="hover:bg-slate-50/60 transition-colors">
                  <td className="py-3 px-4 font-mono font-bold text-slate-800">{item.asvs_id}</td>
                  <td className="py-3 px-4 font-medium text-slate-800">{item.category}</td>
                  <td className="py-3 px-4 text-slate-600 max-w-sm">{item.requirement}</td>
                  <td className="py-3 px-4 whitespace-nowrap">{badge}</td>
                  <td className="py-3 px-4 whitespace-nowrap">
                    <span className="px-2 py-0.5 bg-slate-100 rounded text-slate-600 font-mono text-[11px]">
                      {item.verification_method.replace(/_/g, " ")}
                    </span>
                  </td>
                  <td className="py-3 px-4 text-slate-500 max-w-md">{item.evidence_or_reason}</td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </div>
  );
}
