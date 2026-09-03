import { useEffect, useState } from "react";

import { api, ApiError } from "../api/client";
import type { RedditOpportunity, Site } from "../api/types";
import Badge from "../components/Badge";
import { useSiteContext } from "../siteContext";

export default function Reddit() {
  const { siteId, site } = useSiteContext();
  const [opportunities, setOpportunities] = useState<RedditOpportunity[]>([]);
  const [subreddits, setSubreddits] = useState(site?.subreddits ?? "");
  const [saving, setSaving] = useState(false);
  const [running, setRunning] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const load = () => api.get<RedditOpportunity[]>(`/api/reddit-opportunities?site_id=${siteId}`).then(setOpportunities);

  useEffect(() => {
    load();
  }, [siteId]);

  useEffect(() => {
    setSubreddits(site?.subreddits ?? "");
  }, [site?.subreddits]);

  async function updateStatus(id: number, status: RedditOpportunity["status"]) {
    await api.patch(`/api/reddit-opportunities/${id}`, { status });
    await load();
  }

  async function handleSaveSubreddits() {
    setSaving(true);
    setError(null);
    try {
      await api.patch<Site>(`/api/sites/${siteId}`, { subreddits });
    } catch (err) {
      setError(err instanceof ApiError ? err.message : String(err));
    } finally {
      setSaving(false);
    }
  }

  async function handleRun() {
    setRunning(true);
    setError(null);
    try {
      await api.post("/api/reddit-opportunities/run", { site_id: Number(siteId) });
      await load();
    } catch (err) {
      setError(err instanceof ApiError ? err.message : String(err));
    } finally {
      setRunning(false);
    }
  }

  return (
    <div>
      <h1 className="mb-2 text-xl font-semibold">Reddit Queue</h1>
      <p className="mb-6 text-sm text-slate-500">
        Runs automatically every Monday against your top approved keywords. Drafts are never auto-posted —
        review and mark each one, always by hand.
      </p>

      <div className="mb-6 flex flex-wrap items-end gap-3 rounded-lg border border-slate-200 bg-white p-4">
        <div className="min-w-[300px] flex-1">
          <label className="mb-1 block text-xs font-medium text-slate-500">
            Subreddits to monitor (comma-separated, no "r/")
          </label>
          <input
            className="w-full rounded-md border border-slate-300 px-3 py-2 text-sm"
            value={subreddits}
            onChange={(e) => setSubreddits(e.target.value)}
            placeholder="SaaS, Entrepreneur, marketing"
          />
        </div>
        <button
          className="rounded-md border border-slate-300 px-4 py-2 text-sm font-semibold text-slate-700 hover:bg-slate-50 disabled:opacity-50"
          onClick={handleSaveSubreddits}
          disabled={saving}
        >
          {saving ? "Saving…" : "Save"}
        </button>
        <button
          className="rounded-md bg-brand-green px-4 py-2 text-sm font-semibold text-black disabled:opacity-50"
          onClick={handleRun}
          disabled={running}
        >
          {running ? "Checking…" : "Check now"}
        </button>
      </div>

      {error && <div className="mb-4 rounded-md bg-rose-50 px-4 py-3 text-sm text-rose-700">{error}</div>}

      <div className="space-y-3">
        {opportunities.map((o) => (
          <div key={o.id} className="rounded-lg border border-slate-200 bg-white p-4">
            <div className="mb-2 flex items-center justify-between">
              <div className="text-sm font-medium">
                r/{o.subreddit} — matched "{o.matched_keyword}"
              </div>
              <Badge tone={o.status === "new" ? "warning" : o.status === "replied" ? "positive" : "neutral"}>
                {o.status}
              </Badge>
            </div>
            <a
              href={o.thread_url}
              target="_blank"
              rel="noreferrer"
              className="mb-2 block text-sm text-blue-600 hover:underline"
            >
              {o.thread_url}
            </a>
            {o.draft_reply && (
              <p className="mb-3 rounded-md bg-slate-50 p-3 text-sm text-slate-700">{o.draft_reply}</p>
            )}
            {o.status === "new" && (
              <div className="flex gap-2">
                <button
                  className="rounded-md border border-emerald-300 px-2 py-1 text-xs font-medium text-emerald-700 hover:bg-emerald-50"
                  onClick={() => updateStatus(o.id, "replied")}
                >
                  Mark replied
                </button>
                <button
                  className="rounded-md border border-slate-300 px-2 py-1 text-xs font-medium text-slate-600 hover:bg-slate-50"
                  onClick={() => updateStatus(o.id, "skipped")}
                >
                  Skip
                </button>
              </div>
            )}
          </div>
        ))}
        {opportunities.length === 0 && (
          <div className="rounded-lg border border-dashed border-slate-300 p-8 text-center text-sm text-slate-400">
            No opportunities yet — set subreddits above and click "Check now".
          </div>
        )}
      </div>
    </div>
  );
}
