import { useEffect, useState } from "react";
import { Link } from "react-router-dom";

import { api } from "../api/client";
import type { Article, AuditFinding, GeoMention, Keyword } from "../api/types";
import { DocumentIcon, GlobeIcon, ShieldIcon, TagIcon } from "../components/icons";
import StatCard from "../components/StatCard";
import { useSiteContext } from "../siteContext";

const PIPELINE_STAGES: { key: Keyword["status"]; label: string; color: string }[] = [
  { key: "candidate", label: "Candidate", color: "#F59E0B" },
  { key: "approved", label: "Approved", color: "#0DA678" },
  { key: "published", label: "Published", color: "#2A9BE0" },
  { key: "rejected", label: "Rejected", color: "#CBD5E1" },
];

export default function Overview() {
  const { siteId, site } = useSiteContext();
  const [keywords, setKeywords] = useState<Keyword[]>([]);
  const [articles, setArticles] = useState<Article[]>([]);
  const [findings, setFindings] = useState<AuditFinding[]>([]);
  const [mentions, setMentions] = useState<GeoMention[]>([]);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    Promise.all([
      api.get<Keyword[]>(`/api/keywords?site_id=${siteId}`),
      api.get<Article[]>(`/api/articles?site_id=${siteId}`),
      api.get<AuditFinding[]>(`/api/audit-findings?site_id=${siteId}`),
      api.get<GeoMention[]>(`/api/geo-mentions?site_id=${siteId}`),
    ])
      .then(([k, a, f, m]) => {
        setKeywords(k);
        setArticles(a);
        setFindings(f);
        setMentions(m);
      })
      .catch((err) => setError(String(err)));
  }, [siteId]);

  const candidateCount = keywords.filter((k) => k.status === "candidate").length;
  const openFindings = findings.filter((f) => !f.resolved_at);
  const mentionedCount = mentions.filter((m) => m.mentioned).length;
  const visibilityRate = mentions.length ? Math.round((mentionedCount / mentions.length) * 100) : null;

  const pipelineTotal = keywords.length;
  const pipelineCounts = PIPELINE_STAGES.map((stage) => ({
    ...stage,
    count: keywords.filter((k) => k.status === stage.key).length,
  }));

  const nextSteps = [
    { done: keywords.length > 0, label: "Run keyword research", to: `/dashboard/sites/${siteId}/keywords` },
    { done: keywords.some((k) => k.status === "approved"), label: "Approve at least one keyword", to: `/dashboard/sites/${siteId}/keywords` },
    { done: articles.length > 0, label: "Generate your first article (Module 2 — not built yet)", to: `/dashboard/sites/${siteId}/articles` },
    { done: mentions.length > 0, label: "Set up GEO visibility tracking (Module 4 — not built yet)", to: `/dashboard/sites/${siteId}/geo` },
  ];

  return (
    <div>
      <h1 className="text-xl font-semibold">{site?.name ?? "Overview"}</h1>
      {site && <p className="mb-6 text-sm text-slate-500">{site.url}</p>}
      {!site && <div className="mb-6" />}

      {error && (
        <div className="mb-4 rounded-md bg-rose-50 px-4 py-3 text-sm text-rose-700">
          Couldn't reach the API — is the backend running? ({error})
        </div>
      )}

      <div className="mb-6 grid grid-cols-2 gap-4 md:grid-cols-4">
        <StatCard label="Keywords awaiting review" value={candidateCount} hint={`${keywords.length} total`} accent="green" icon={<TagIcon />} />
        <StatCard
          label="Articles in draft/review"
          value={articles.filter((a) => a.status !== "published").length}
          hint={`${articles.length} total`}
          accent="blue"
          icon={<DocumentIcon />}
        />
        <StatCard label="Open technical issues" value={openFindings.length} hint={`${findings.length} total`} accent="green" icon={<ShieldIcon />} />
        <StatCard
          label="AI-search visibility"
          value={visibilityRate === null ? "—" : `${visibilityRate}%`}
          hint={mentions.length ? `${mentionedCount}/${mentions.length} checks mentioned you` : "no checks yet"}
          accent="blue"
          icon={<GlobeIcon />}
        />
      </div>

      <div className="grid grid-cols-1 gap-4 lg:grid-cols-5">
        <div className="rounded-lg border border-slate-200 bg-white p-5 lg:col-span-3">
          <div className="mb-4 text-xs font-medium uppercase tracking-wide text-slate-500">Keyword pipeline</div>
          {pipelineTotal === 0 ? (
            <p className="text-sm text-slate-400">No keywords yet.</p>
          ) : (
            <>
              <div className="flex h-3 w-full overflow-hidden rounded-sm">
                {pipelineCounts
                  .filter((s) => s.count > 0)
                  .map((s) => (
                    <div
                      key={s.key}
                      style={{ width: `${(s.count / pipelineTotal) * 100}%`, backgroundColor: s.color }}
                      title={`${s.label}: ${s.count}`}
                    />
                  ))}
              </div>
              <div className="mt-4 flex flex-wrap gap-x-6 gap-y-2">
                {pipelineCounts.map((s) => (
                  <div key={s.key} className="flex items-center gap-2 text-xs text-slate-600">
                    <span className="h-2 w-2 rounded-full" style={{ backgroundColor: s.color }} />
                    {s.label} <span className="font-medium text-slate-900">{s.count}</span>
                  </div>
                ))}
              </div>
            </>
          )}
        </div>

        <div className="rounded-lg border border-slate-200 bg-white p-5 lg:col-span-2">
          <div className="mb-4 text-xs font-medium uppercase tracking-wide text-slate-500">Next steps</div>
          <ul className="space-y-3">
            {nextSteps.map((step) => (
              <li key={step.label} className="flex items-start gap-2 text-sm">
                <span
                  className={`mt-0.5 flex h-4 w-4 shrink-0 items-center justify-center rounded-full text-[10px] ${
                    step.done ? "bg-brand-green text-white" : "border border-slate-300 text-transparent"
                  }`}
                >
                  ✓
                </span>
                {step.done ? (
                  <span className="text-slate-400 line-through">{step.label}</span>
                ) : (
                  <Link to={step.to} className="text-slate-700 hover:text-brand-green">
                    {step.label}
                  </Link>
                )}
              </li>
            ))}
          </ul>
        </div>
      </div>
    </div>
  );
}
