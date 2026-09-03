import { useEffect, useState } from "react";

import { api } from "../api/client";
import type { Article, AuditFinding, GeoMention, Keyword } from "../api/types";
import StatCard from "../components/StatCard";

export default function Overview() {
  const [keywords, setKeywords] = useState<Keyword[]>([]);
  const [articles, setArticles] = useState<Article[]>([]);
  const [findings, setFindings] = useState<AuditFinding[]>([]);
  const [mentions, setMentions] = useState<GeoMention[]>([]);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    Promise.all([
      api.get<Keyword[]>("/api/keywords"),
      api.get<Article[]>("/api/articles"),
      api.get<AuditFinding[]>("/api/audit-findings"),
      api.get<GeoMention[]>("/api/geo-mentions"),
    ])
      .then(([k, a, f, m]) => {
        setKeywords(k);
        setArticles(a);
        setFindings(f);
        setMentions(m);
      })
      .catch((err) => setError(String(err)));
  }, []);

  const openFindings = findings.filter((f) => !f.resolved_at);
  const mentionedCount = mentions.filter((m) => m.mentioned).length;
  const visibilityRate = mentions.length ? Math.round((mentionedCount / mentions.length) * 100) : null;

  return (
    <div>
      <h1 className="mb-6 text-xl font-semibold">Overview</h1>
      {error && (
        <div className="mb-4 rounded-md bg-rose-50 px-4 py-3 text-sm text-rose-700">
          Couldn't reach the API — is the backend running? ({error})
        </div>
      )}
      <div className="grid grid-cols-2 gap-4 md:grid-cols-4">
        <StatCard
          label="Keywords awaiting review"
          value={keywords.filter((k) => k.status === "candidate").length}
          hint={`${keywords.length} total`}
        />
        <StatCard
          label="Articles in draft/review"
          value={articles.filter((a) => a.status !== "published").length}
          hint={`${articles.length} total`}
        />
        <StatCard label="Open technical issues" value={openFindings.length} hint={`${findings.length} total`} />
        <StatCard
          label="AI-search visibility"
          value={visibilityRate === null ? "—" : `${visibilityRate}%`}
          hint={mentions.length ? `${mentionedCount}/${mentions.length} checks mentioned you` : "no checks yet"}
        />
      </div>
    </div>
  );
}
