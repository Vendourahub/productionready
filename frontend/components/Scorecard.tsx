interface ScorecardProps {
  readinessStatus: string;
  blockersCount: number;
  totalFindingsCount: number;
  verifiedControlsCount: number;
  unverifiedGapsCount: number;
}

export default function Scorecard({
  readinessStatus,
  blockersCount,
  totalFindingsCount,
  verifiedControlsCount,
  unverifiedGapsCount,
}: ScorecardProps) {
  const getBannerColor = (status: string) => {
    switch (status) {
      case "NOT PRODUCTION READY":
        return "bg-red-600 text-white border-red-700";
      case "NEEDS REMEDIATION":
        return "bg-amber-600 text-white border-amber-700";
      default:
        return "bg-emerald-600 text-white border-emerald-700";
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-center justify-between gap-4 p-5 bg-white border border-slate-200 rounded-xl shadow-sm">
        <div>
          <span className="text-xs font-semibold text-slate-500 uppercase tracking-wider">
            Deployment Readiness Verdict
          </span>
          <div className="text-2xl font-black text-slate-900 mt-1">
            {readinessStatus}
          </div>
        </div>
        <div
          className={`px-4 py-1.5 rounded-full text-xs font-bold tracking-wider border ${getBannerColor(
            readinessStatus
          )}`}
        >
          {readinessStatus}
        </div>
      </div>

      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-sm text-center">
          <div className="text-3xl font-extrabold text-red-600">{blockersCount}</div>
          <div className="text-xs font-semibold uppercase tracking-wider text-slate-500 mt-1">
            Launch Blockers
          </div>
        </div>

        <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-sm text-center">
          <div className="text-3xl font-extrabold text-slate-800">{totalFindingsCount}</div>
          <div className="text-xs font-semibold uppercase tracking-wider text-slate-500 mt-1">
            Total Findings
          </div>
        </div>

        <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-sm text-center">
          <div className="text-3xl font-extrabold text-emerald-600">{verifiedControlsCount}</div>
          <div className="text-xs font-semibold uppercase tracking-wider text-slate-500 mt-1">
            ASVS Verified Clean
          </div>
        </div>

        <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-sm text-center">
          <div className="text-3xl font-extrabold text-amber-600">{unverifiedGapsCount}</div>
          <div className="text-xs font-semibold uppercase tracking-wider text-slate-500 mt-1">
            Unverified Gaps
          </div>
        </div>
      </div>
    </div>
  );
}
