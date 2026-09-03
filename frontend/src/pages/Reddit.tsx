import { useEffect, useState } from "react";

import { api } from "../api/client";
import type { RedditOpportunity } from "../api/types";
import Badge from "../components/Badge";

export default function Reddit() {
  const [opportunities, setOpportunities] = useState<RedditOpportunity[]>([]);

  const load = () => api.get<RedditOpportunity[]>("/api/reddit-opportunities").then(setOpportunities);

  useEffect(() => {
    load();
  }, []);

  async function updateStatus(id: number, status: RedditOpportunity["status"]) {
    await api.patch(`/api/reddit-opportunities/${id}`, { status });
    await load();
  }

  return (
    <div>
      <h1 className="mb-2 text-xl font-semibold">Reddit Queue</h1>
      <p className="mb-6 text-sm text-slate-500">
        Module 5 (subreddit monitor) isn't built yet. Drafts are never auto-posted — review and mark each
        one, always by hand.
      </p>
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
            No opportunities yet.
          </div>
        )}
      </div>
    </div>
  );
}
