import { useEffect, useState } from "react";

import { api, ApiError } from "../api/client";
import type { Keyword, Site } from "../api/types";
import Badge from "../components/Badge";

const STATUS_TONE: Record<Keyword["status"], "neutral" | "positive" | "negative" | "warning"> = {
  candidate: "warning",
  approved: "positive",
  rejected: "negative",
  published: "neutral",
};

export default function Keywords() {
  const [sites, setSites] = useState<Site[]>([]);
  const [selectedSiteId, setSelectedSiteId] = useState<number | null>(null);
  const [keywords, setKeywords] = useState<Keyword[]>([]);
  const [statusFilter, setStatusFilter] = useState<"all" | Keyword["status"]>("candidate");
  const [running, setRunning] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const [newSiteUrl, setNewSiteUrl] = useState("");
  const [newSiteName, setNewSiteName] = useState("");

  const loadSites = () => api.get<Site[]>("/api/sites").then(setSites);
  const loadKeywords = (siteId: number) =>
    api.get<Keyword[]>(`/api/keywords?site_id=${siteId}`).then(setKeywords);

  useEffect(() => {
    loadSites().catch((err) => setError(String(err)));
  }, []);

  useEffect(() => {
    if (selectedSiteId === null && sites.length > 0) setSelectedSiteId(sites[0].id);
  }, [sites, selectedSiteId]);

  useEffect(() => {
    if (selectedSiteId !== null) loadKeywords(selectedSiteId).catch((err) => setError(String(err)));
  }, [selectedSiteId]);

  async function handleCreateSite(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    try {
      const site = await api.post<Site>("/api/sites", { url: newSiteUrl, name: newSiteName });
      setNewSiteUrl("");
      setNewSiteName("");
      await loadSites();
      setSelectedSiteId(site.id);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : String(err));
    }
  }

  async function handleRunResearch() {
    if (selectedSiteId === null) return;
    setRunning(true);
    setError(null);
    try {
      await api.post("/api/keywords/research", { site_id: selectedSiteId });
      await loadKeywords(selectedSiteId);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : String(err));
    } finally {
      setRunning(false);
    }
  }

  async function handleStatusChange(id: number, status: Keyword["status"]) {
    await api.patch<Keyword>(`/api/keywords/${id}`, { status });
    if (selectedSiteId !== null) await loadKeywords(selectedSiteId);
  }

  const visibleKeywords = keywords.filter((k) => statusFilter === "all" || k.status === statusFilter);

  return (
    <div>
      <h1 className="mb-6 text-xl font-semibold">Keywords</h1>

      {error && (
        <div className="mb-4 rounded-md bg-rose-50 px-4 py-3 text-sm text-rose-700">{error}</div>
      )}

      <div className="mb-6 flex flex-wrap items-end gap-4 rounded-lg border border-slate-200 bg-white p-4">
        <div>
          <label className="mb-1 block text-xs font-medium text-slate-500">Site</label>
          <select
            className="rounded-md border border-slate-300 px-3 py-1.5 text-sm"
            value={selectedSiteId ?? ""}
            onChange={(e) => setSelectedSiteId(Number(e.target.value))}
          >
            {sites.map((site) => (
              <option key={site.id} value={site.id}>
                {site.name} ({site.url})
              </option>
            ))}
          </select>
        </div>
        <button
          className="rounded-md bg-slate-900 px-4 py-1.5 text-sm font-medium text-white disabled:opacity-50"
          onClick={handleRunResearch}
          disabled={selectedSiteId === null || running}
        >
          {running ? "Running keyword research…" : "Run keyword research"}
        </button>

        <form onSubmit={handleCreateSite} className="ml-auto flex items-end gap-2">
          <div>
            <label className="mb-1 block text-xs font-medium text-slate-500">Add site — name</label>
            <input
              className="rounded-md border border-slate-300 px-3 py-1.5 text-sm"
              value={newSiteName}
              onChange={(e) => setNewSiteName(e.target.value)}
              placeholder="Acme Co"
              required
            />
          </div>
          <div>
            <label className="mb-1 block text-xs font-medium text-slate-500">URL</label>
            <input
              className="rounded-md border border-slate-300 px-3 py-1.5 text-sm"
              value={newSiteUrl}
              onChange={(e) => setNewSiteUrl(e.target.value)}
              placeholder="https://acme.com"
              required
            />
          </div>
          <button className="rounded-md border border-slate-300 px-3 py-1.5 text-sm font-medium">Add</button>
        </form>
      </div>

      <div className="mb-3 flex gap-2">
        {(["candidate", "approved", "rejected", "published", "all"] as const).map((s) => (
          <button
            key={s}
            onClick={() => setStatusFilter(s)}
            className={`rounded-full px-3 py-1 text-xs font-medium ${
              statusFilter === s ? "bg-slate-900 text-white" : "bg-slate-100 text-slate-600"
            }`}
          >
            {s}
          </button>
        ))}
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
                  No keywords yet — pick a site and run keyword research.
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}
