import { useEffect, useMemo, useState } from "react";
import { CartesianGrid, Line, LineChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";

import { api } from "../api/client";
import type { GeoMention } from "../api/types";
import Badge from "../components/Badge";
import { useSiteContext } from "../siteContext";

export default function Geo() {
  const { siteId } = useSiteContext();
  const [mentions, setMentions] = useState<GeoMention[]>([]);

  useEffect(() => {
    api.get<GeoMention[]>(`/api/geo-mentions?site_id=${siteId}`).then(setMentions);
  }, [siteId]);

  const chartData = useMemo(() => {
    // Bucket by check date, one visibility-rate line overall (per-provider
    // breakdown lives in the table below). Rebuild once real data exists.
    const byDate = new Map<string, { total: number; mentioned: number }>();
    for (const m of mentions) {
      const day = m.checked_at.slice(0, 10);
      const bucket = byDate.get(day) ?? { total: 0, mentioned: 0 };
      bucket.total += 1;
      if (m.mentioned) bucket.mentioned += 1;
      byDate.set(day, bucket);
    }
    return Array.from(byDate.entries())
      .sort(([a], [b]) => a.localeCompare(b))
      .map(([date, { total, mentioned }]) => ({
        date,
        visibilityRate: Math.round((mentioned / total) * 100),
      }));
  }, [mentions]);

  const notMentioned = mentions.filter((m) => !m.mentioned);

  return (
    <div>
      <h1 className="mb-2 text-xl font-semibold">GEO Tracker</h1>
      <p className="mb-6 text-sm text-slate-500">
        Module 4 (ChatGPT/Claude/Gemini/Perplexity querying) isn't built yet — set up provider keys and this
        fills in on the first weekly run.
      </p>

      <div className="mb-6 rounded-lg border border-slate-200 bg-white p-4">
        <div className="mb-2 text-xs font-medium uppercase tracking-wide text-slate-500">
          Visibility over time
        </div>
        {chartData.length > 0 ? (
          <ResponsiveContainer width="100%" height={220}>
            <LineChart data={chartData}>
              <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
              <XAxis dataKey="date" fontSize={12} />
              <YAxis fontSize={12} unit="%" domain={[0, 100]} />
              <Tooltip />
              <Line type="monotone" dataKey="visibilityRate" stroke="#0DA678" strokeWidth={2} dot={false} />
            </LineChart>
          </ResponsiveContainer>
        ) : (
          <div className="flex h-[220px] items-center justify-center text-sm text-slate-400">
            No GEO checks recorded yet.
          </div>
        )}
      </div>

      <div className="overflow-hidden rounded-lg border border-slate-200 bg-white">
        <div className="border-b border-slate-200 px-4 py-2 text-xs font-medium uppercase tracking-wide text-slate-500">
          Not yet mentioned — prioritize for content
        </div>
        <table className="w-full text-sm">
          <thead className="border-b border-slate-200 bg-slate-50 text-left text-xs uppercase text-slate-500">
            <tr>
              <th className="px-4 py-2">Query</th>
              <th className="px-4 py-2">Provider</th>
              <th className="px-4 py-2">Competitors mentioned</th>
              <th className="px-4 py-2">Checked</th>
            </tr>
          </thead>
          <tbody>
            {notMentioned.map((m) => (
              <tr key={m.id} className="border-b border-slate-100 last:border-0">
                <td className="px-4 py-2 font-medium">{m.query}</td>
                <td className="px-4 py-2">
                  <Badge>{m.provider}</Badge>
                </td>
                <td className="px-4 py-2 text-slate-500">{(m.competitors_mentioned ?? []).join(", ") || "—"}</td>
                <td className="px-4 py-2 text-slate-400">{new Date(m.checked_at).toLocaleDateString()}</td>
              </tr>
            ))}
            {notMentioned.length === 0 && (
              <tr>
                <td colSpan={4} className="px-4 py-8 text-center text-slate-400">
                  Nothing to prioritize yet.
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}
