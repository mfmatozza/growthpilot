import { useEffect, useState } from "react";

import { api, ApiError } from "../api/client";
import type { Keyword } from "../api/types";
import Badge from "../components/Badge";
import { useSiteContext } from "../siteContext";

const STATUS_TONE: Record<Keyword["status"], "neutral" | "positive" | "negative" | "warning"> = {
  candidate: "warning",
  approved: "positive",
  rejected: "negative",
  published: "neutral",
};

export default function Keywords() {
  const { siteId } = useSiteContext();
  const [keywords, setKeywords] = useState<Keyword[]>([]);
  const [statusFilter, setStatusFilter] = useState<"all" | Keyword["status"]>("candidate");
  const [running, setRunning] = useState(false);
  const [approvingAll, setApprovingAll] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const loadKeywords = () => api.get<Keyword[]>(`/api/keywords?site_id=${siteId}`).then(setKeywords);

  useEffect(() => {
    loadKeywords().catch((err) => setError(err instanceof ApiError ? err.message : String(err)));
  }, [siteId]);

  async function handleRunResearch() {
    setRunning(true);
    setError(null);
    try {
      await api.post("/api/keywords/research", { site_id: Number(siteId) });
      await loadKeywords();
    } catch (err) {
      setError(err instanceof ApiError ? err.message : String(err));
    } finally {
      setRunning(false);
    }
  }

  async function handleStatusChange(id: number, status: Keyword["status"]) {
    await api.patch<Keyword>(`/api/keywords/${id}`, { status });
    await loadKeywords();
  }

  async function handleApproveAll() {
    setApprovingAll(true);
    setError(null);
    try {
      await api.post("/api/keywords/approve-all", { site_id: Number(siteId) });
      await loadKeywords();
    } catch (err) {
      setError(err instanceof ApiError ? err.message : String(err));
    } finally {
      setApprovingAll(false);
    }
  }

  const visibleKeywords = keywords.filter((k) => statusFilter === "all" || k.status === statusFilter);
  const candidateCount = keywords.filter((k) => k.status === "candidate").length;

  return (
    <div>
      <div className="mb-6 flex items-center justify-between">
        <h1 className="text-xl font-semibold">Keywords</h1>
        <button
          className="rounded-md bg-brand-green px-4 py-2 text-sm font-semibold text-black disabled:opacity-50"
          onClick={handleRunResearch}
          disabled={running}
        >
          {running ? "Running keyword research…" : "Run keyword research"}
        </button>
      </div>

      {error && <div className="mb-4 rounded-md bg-rose-50 px-4 py-3 text-sm text-rose-700">{error}</div>}

      <div className="mb-3 flex items-center justify-between">
        <div className="flex gap-2">
          {(["candidate", "approved", "rejected", "published", "all"] as const).map((s) => (
            <button
              key={s}
              onClick={() => setStatusFilter(s)}
              className={`rounded-full px-3 py-1 text-xs font-medium ${
                statusFilter === s ? "bg-brand-green text-black" : "bg-slate-100 text-slate-600"
              }`}
            >
              {s}
            </button>
          ))}
        </div>
        {candidateCount > 0 && (
          <button
            onClick={handleApproveAll}
            disabled={approvingAll}
            className="rounded-md border border-emerald-300 px-3 py-1.5 text-xs font-medium text-emerald-700 hover:bg-emerald-50 disabled:opacity-50"
          >
            {approvingAll ? "Approving…" : `Approve all (${candidateCount})`}
          </button>
        )}
      </div>

      <div className="overflow-hidden rounded-lg border border-slate-200 bg-white">
        <table className="w-full text-sm">
          <thead className="border-b border-slate-200 bg-slate-50 text-left text-xs uppercase text-slate-500">
            <tr>
              <th className="px-4 py-2">Keyword</th>
              <th className="px-4 py-2">Rationale</th>
              <th className="px-4 py-2">Volume</th>
              <th className="px-4 py-2">Difficulty</th>
              <th className="px-4 py-2">Opportunity</th>
              <th className="px-4 py-2">Status</th>
              <th className="px-4 py-2">Actions</th>
            </tr>
          </thead>
          <tbody>
            {visibleKeywords.map((k) => (
              <tr key={k.id} className="border-b border-slate-100 last:border-0">
                <td className="max-w-xs px-4 py-2 font-medium">{k.keyword}</td>
                <td className="max-w-md px-4 py-2 text-slate-500">{k.rationale}</td>
                <td className="px-4 py-2">{k.volume ?? "—"}</td>
                <td className="px-4 py-2">{k.difficulty ?? "—"}</td>
                <td className="px-4 py-2 font-medium">{k.opportunity_score ?? "—"}</td>
                <td className="px-4 py-2">
                  <Badge tone={STATUS_TONE[k.status]}>{k.status}</Badge>
                </td>
                <td className="px-4 py-2">
                  {k.status === "candidate" && (
                    <div className="flex gap-2">
                      <button
                        className="rounded-md border border-emerald-300 px-2 py-1 text-xs font-medium text-emerald-700 hover:bg-emerald-50"
                        onClick={() => handleStatusChange(k.id, "approved")}
                      >
                        Approve
                      </button>
                      <button
                        className="rounded-md border border-rose-300 px-2 py-1 text-xs font-medium text-rose-700 hover:bg-rose-50"
                        onClick={() => handleStatusChange(k.id, "rejected")}
                      >
                        Reject
                      </button>
                    </div>
                  )}
                </td>
              </tr>
            ))}
            {visibleKeywords.length === 0 && (
              <tr>
                <td colSpan={7} className="px-4 py-8 text-center text-slate-400">
                  No keywords yet — run keyword research to get started.
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}
