"use client";
import { useEffect, useState } from "react";
import Link from "next/link";
import { Project, fetchProjects, createProject, triggerAssessment } from "@/lib/api";

export default function ProjectsPage() {
  const [projects, setProjects] = useState<Project[]>([]);
  const [loading, setLoading] = useState(true);
  const [showModal, setShowModal] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [runningId, setRunningId] = useState<string | null>(null);

  const [name, setName] = useState("");
  const [repoUrl, setRepoUrl] = useState("");
  const [branch, setBranch] = useState("main");

  const load = async () => {
    try {
      const data = await fetchProjects();
      setProjects(data);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    load();
  }, []);

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault();
    setSubmitting(true);
    try {
      await createProject({ name, repository_url: repoUrl, default_branch: branch });
      setName("");
      setRepoUrl("");
      setBranch("main");
      setShowModal(false);
      await load();
    } catch (err) {
      alert("Failed to connect repository");
    } finally {
      setSubmitting(false);
    }
  };

  const handleRunAssessment = async (projectId: string) => {
    setRunningId(projectId);
    try {
      const assessment = await triggerAssessment(projectId);
      window.location.href = `/assessments/${assessment.id}`;
    } catch (err) {
      alert("Assessment execution failed");
    } finally {
      setRunningId(null);
    }
  };

  return (
    <div className="space-y-8">
      {/* Hero Banner */}
      <div className="bg-slate-900 rounded-2xl p-8 text-white shadow-xl flex flex-wrap items-center justify-between gap-6 border border-slate-800">
        <div className="max-w-2xl">
          <span className="text-xs font-bold tracking-widest text-sky-400 uppercase bg-slate-800 px-3 py-1 rounded-full border border-slate-700">
            Phase 2 Commercial Foundation
          </span>
          <h1 className="text-3xl font-extrabold tracking-tight mt-3">
            Projects & Verification Intake
          </h1>
          <p className="text-slate-300 text-sm mt-2 leading-relaxed">
            Connect an authorized GitHub repository or local codebase. Run deterministic security checks, verify database RLS, and generate prioritized remediation evidence.
          </p>
        </div>
        <div>
          <button
            onClick={() => setShowModal(true)}
            className="px-5 py-2.5 bg-sky-500 hover:bg-sky-400 text-slate-950 font-bold rounded-xl shadow-lg transition-all text-sm"
          >
            + Connect Repository
          </button>
        </div>
      </div>

      {/* Projects Table */}
      <div className="bg-white border border-slate-200 rounded-xl shadow-sm overflow-hidden">
        <div className="p-5 border-b border-slate-200 flex items-center justify-between">
          <h2 className="text-base font-bold text-slate-900">Connected Repositories</h2>
          <span className="text-xs text-slate-500 font-mono">{projects.length} Registered</span>
        </div>

        {loading ? (
          <div className="p-12 text-center text-slate-500 text-sm">Loading projects...</div>
        ) : projects.length === 0 ? (
          <div className="p-12 text-center space-y-3">
            <div className="text-slate-400 text-sm">No repositories connected yet.</div>
            <button
              onClick={() => setShowModal(true)}
              className="text-xs text-sky-600 font-semibold hover:underline"
            >
              Connect your first repository &rarr;
            </button>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs border-collapse">
              <thead>
                <tr className="bg-slate-50 border-b border-slate-200 text-slate-600 font-bold uppercase tracking-wider">
                  <th className="py-3 px-4">Project Name</th>
                  <th className="py-3 px-4">Repository URL / Location</th>
                  <th className="py-3 px-4">Default Branch</th>
                  <th className="py-3 px-4">Latest Verdict</th>
                  <th className="py-3 px-4 text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {projects.map((p) => (
                  <tr key={p.id} className="hover:bg-slate-50/60 transition-colors">
                    <td className="py-3.5 px-4 font-bold text-slate-900">{p.name}</td>
                    <td className="py-3.5 px-4 font-mono text-slate-600 truncate max-w-xs">
                      {p.repository_url}
                    </td>
                    <td className="py-3.5 px-4">
                      <span className="px-2 py-0.5 bg-slate-100 rounded text-slate-700 font-mono">
                        {p.default_branch}
                      </span>
                    </td>
                    <td className="py-3.5 px-4">
                      {p.latest_readiness_status ? (
                        <span
                          className={`inline-block px-2 py-0.5 rounded-full font-bold text-[10px] ${
                            p.latest_readiness_status === "NOT PRODUCTION READY"
                              ? "bg-red-50 text-red-700 border border-red-200"
                              : p.latest_readiness_status === "NEEDS REMEDIATION"
                              ? "bg-amber-50 text-amber-700 border border-amber-200"
                              : "bg-emerald-50 text-emerald-700 border border-emerald-200"
                          }`}
                        >
                          {p.latest_readiness_status}
                        </span>
                      ) : (
                        <span className="text-slate-400 text-[11px]">Unassessed</span>
                      )}
                    </td>
                    <td className="py-3.5 px-4 text-right space-x-2">
                      <button
                        disabled={runningId === p.id}
                        onClick={() => handleRunAssessment(p.id)}
                        className="px-3 py-1 bg-slate-900 hover:bg-slate-800 text-white font-semibold rounded-lg text-xs transition-colors disabled:opacity-50"
                      >
                        {runningId === p.id ? "Auditing..." : "Run Assessment"}
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Connect Modal */}
      {showModal && (
        <div className="fixed inset-0 bg-slate-900/60 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <div className="bg-white rounded-2xl max-w-md w-full p-6 shadow-2xl border border-slate-200">
            <h3 className="text-lg font-bold text-slate-900 mb-1">Connect Repository</h3>
            <p className="text-xs text-slate-500 mb-4">
              Enter GitHub repository URL (e.g. https://github.com/owner/repo) or a local filesystem path.
            </p>

            <form onSubmit={handleCreate} className="space-y-4 text-xs">
              <div>
                <label className="block font-semibold text-slate-700 mb-1">Project Name</label>
                <input
                  type="text"
                  required
                  placeholder="e.g. Client SaaS Deliverable"
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  className="w-full px-3 py-2 border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-sky-500"
                />
              </div>

              <div>
                <label className="block font-semibold text-slate-700 mb-1">
                  Repository URL / Local Path
                </label>
                <input
                  type="text"
                  required
                  placeholder="https://github.com/agency/client-app"
                  value={repoUrl}
                  onChange={(e) => setRepoUrl(e.target.value)}
                  className="w-full px-3 py-2 border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-sky-500 font-mono"
                />
              </div>

              <div>
                <label className="block font-semibold text-slate-700 mb-1">Default Branch</label>
                <input
                  type="text"
                  value={branch}
                  onChange={(e) => setBranch(e.target.value)}
                  className="w-full px-3 py-2 border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-sky-500 font-mono"
                />
              </div>

              <div className="flex justify-end gap-2 pt-3 border-t border-slate-100">
                <button
                  type="button"
                  onClick={() => setShowModal(false)}
                  className="px-4 py-2 bg-slate-100 hover:bg-slate-200 text-slate-700 font-semibold rounded-lg transition-colors"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={submitting}
                  className="px-4 py-2 bg-sky-600 hover:bg-sky-500 text-white font-semibold rounded-lg transition-colors disabled:opacity-50"
                >
                  {submitting ? "Connecting..." : "Confirm & Save"}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
