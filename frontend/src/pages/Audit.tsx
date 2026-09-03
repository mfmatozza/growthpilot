import { useEffect, useState } from "react";

import { api, ApiError } from "../api/client";
import type { AuditFinding, Severity } from "../api/types";
import Badge from "../components/Badge";
import { useSiteContext } from "../siteContext";

const SEVERITY_TONE: Record<Severity, "neutral" | "positive" | "negative" | "warning"> = {
  critical: "negative",
  high: "negative",
  medium: "warning",
  low: "neutral",
};

export default function Audit() {
  const { siteId } = useSiteContext();
  const [findings, setFindings] = useState<AuditFinding[]>([]);
  const [running, setRunning] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const load = () => api.get<AuditFinding[]>(`/api/audit-findings?site_id=${siteId}`).then(setFindings);

  useEffect(() => {
    load();
  }, [siteId]);

  async function handleRun() {
    setRunning(true);
    setError(null);
    try {
      await api.post("/api/audit-findings/run", { site_id: Number(siteId) });
      await load();
    } catch (err) {
      setError(err instanceof ApiError ? err.message : String(err));
    } finally {
      setRunning(false);
    }
  }

  async function handleExport() {
    setError(null);
    try {
      await api.download(`/api/audit-findings/export?site_id=${siteId}`, `audit-findings-site-${siteId}.csv`);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : String(err));
    }
  }

  const open = findings.filter((f) => !f.resolved_at);

  return (
    <div>
      <div className="mb-2 flex items-center justify-between">
        <h1 className="text-xl font-semibold">Technical Audit</h1>
        <div className="flex gap-2">
          <button
            className="rounded-md border border-slate-300 px-4 py-2 text-sm font-semibold text-slate-700 hover:bg-slate-50"
            onClick={handleExport}
          >
            Export CSV
          </button>
          <button
            className="rounded-md bg-brand-green px-4 py-2 text-sm font-semibold text-black disabled:opacity-50"
            onClick={handleRun}
            disabled={running}
          >
            {running ? "Running audit…" : "Run audit now"}
          </button>
        </div>
      </div>
      <p className="mb-6 text-sm text-slate-500">
        Runs automatically every Monday. A crawl (broken links, missing titles/meta/alt text, duplicate
        titles) plus a PageSpeed Insights pass, summarized and ranked by severity. The table below shows
        open issues only — "Export CSV" includes resolved ones too, for a full record.
      </p>

      {error && <div className="mb-4 rounded-md bg-rose-50 px-4 py-3 text-sm text-rose-700">{error}</div>}

      <div className="overflow-hidden rounded-lg border border-slate-200 bg-white">
        <table className="w-full text-sm">
          <thead className="border-b border-slate-200 bg-slate-50 text-left text-xs uppercase text-slate-500">
            <tr>
              <th className="px-4 py-2">Severity</th>
              <th className="px-4 py-2">Page</th>
              <th className="px-4 py-2">Description</th>
              <th className="px-4 py-2">First seen</th>
            </tr>
          </thead>
          <tbody>
            {open.map((f) => (
              <tr key={f.id} className="border-b border-slate-100 last:border-0">
                <td className="px-4 py-2">
                  <Badge tone={SEVERITY_TONE[f.severity]}>{f.severity}</Badge>
                </td>
                <td className="max-w-xs truncate px-4 py-2">{f.page}</td>
                <td className="px-4 py-2 text-slate-600">{f.description}</td>
                <td className="px-4 py-2 text-slate-400">{new Date(f.first_seen).toLocaleDateString()}</td>
              </tr>
            ))}
            {open.length === 0 && (
              <tr>
                <td colSpan={4} className="px-4 py-8 text-center text-slate-400">
                  No open issues — run an audit to check.
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}
