import { useEffect, useState } from "react";

import { api } from "../api/client";
import type { AuditFinding, Severity } from "../api/types";
import Badge from "../components/Badge";

const SEVERITY_TONE: Record<Severity, "neutral" | "positive" | "negative" | "warning"> = {
  critical: "negative",
  high: "negative",
  medium: "warning",
  low: "neutral",
};

export default function Audit() {
  const [findings, setFindings] = useState<AuditFinding[]>([]);

  useEffect(() => {
    api.get<AuditFinding[]>("/api/audit-findings").then(setFindings);
  }, []);

  const open = findings.filter((f) => !f.resolved_at);

  return (
    <div>
      <h1 className="mb-2 text-xl font-semibold">Technical Audit</h1>
      <p className="mb-6 text-sm text-slate-500">
        Module 3 (Lighthouse + crawl auditor) isn't built yet — this will populate on its weekly run.
      </p>
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
                  No open issues.
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}
