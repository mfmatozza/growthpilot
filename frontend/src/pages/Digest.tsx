import { useEffect, useMemo, useState } from "react";

import { api } from "../api/client";
import type { Article, AuditFinding, GeoMention, Keyword, RedditOpportunity } from "../api/types";
import { useSiteContext } from "../siteContext";

type SectionKey = "keywords" | "articles" | "audit" | "geo" | "reddit";

const SECTIONS: { key: SectionKey; label: string }[] = [
  { key: "keywords", label: "Keywords awaiting review" },
  { key: "articles", label: "Draft/review articles" },
  { key: "audit", label: "Open technical issues" },
  { key: "geo", label: "GEO visibility gaps" },
  { key: "reddit", label: "New Reddit opportunities" },
];

export default function Digest() {
  const { siteId, site } = useSiteContext();
  const [included, setIncluded] = useState<Record<SectionKey, boolean>>({
    keywords: true,
    articles: true,
    audit: true,
    geo: true,
    reddit: true,
  });
  const [keywords, setKeywords] = useState<Keyword[]>([]);
  const [articles, setArticles] = useState<Article[]>([]);
  const [findings, setFindings] = useState<AuditFinding[]>([]);
  const [mentions, setMentions] = useState<GeoMention[]>([]);
  const [opportunities, setOpportunities] = useState<RedditOpportunity[]>([]);
  const [copyLabel, setCopyLabel] = useState("Copy prompt");

  useEffect(() => {
    api.get<Keyword[]>(`/api/keywords?site_id=${siteId}&status=candidate`).then(setKeywords);
    api.get<Article[]>(`/api/articles?site_id=${siteId}`).then(setArticles);
    api.get<AuditFinding[]>(`/api/audit-findings?site_id=${siteId}`).then(setFindings);
    api.get<GeoMention[]>(`/api/geo-mentions?site_id=${siteId}`).then(setMentions);
    api.get<RedditOpportunity[]>(`/api/reddit-opportunities?site_id=${siteId}`).then(setOpportunities);
  }, [siteId]);

  const unpublishedArticles = articles.filter((a) => a.status !== "published");
  const openFindings = findings.filter((f) => !f.resolved_at);
  const notMentioned = mentions.filter((m) => !m.mentioned);
  const mentionRate = mentions.length ? Math.round(((mentions.length - notMentioned.length) / mentions.length) * 100) : null;
  const newOpportunities = opportunities.filter((o) => o.status === "new");

  const prompt = useMemo(() => {
    const lines: string[] = [
      `You're continuing SEO/GEO work on GrowthPilot for ${site?.name ?? "this site"} (${site?.url ?? ""}).`,
      `Here's the current state, review it and tell me what you'd tackle first, or just dig in.`,
    ];

    if (included.keywords) {
      lines.push(`\n## Keywords awaiting review (${keywords.length})`);
      if (keywords.length === 0) lines.push("None pending.");
      for (const k of keywords.slice(0, 30)) {
        lines.push(`- "${k.keyword}" (opportunity: ${k.opportunity_score ?? "—"}): ${k.rationale ?? ""}`);
      }
    }

    if (included.articles) {
      lines.push(`\n## Draft/review articles (${unpublishedArticles.length})`);
      if (unpublishedArticles.length === 0) lines.push("None in progress.");
      for (const a of unpublishedArticles) {
        lines.push(`- "${a.title}" (${a.status}, ${a.article_type}), /${a.slug}`);
      }
    }

    if (included.audit) {
      lines.push(`\n## Open technical issues (${openFindings.length})`);
      if (openFindings.length === 0) lines.push("None open.");
      for (const f of openFindings) {
        lines.push(`- [${f.severity}] ${f.page}: ${f.description}`);
      }
    }

    if (included.geo) {
      lines.push(`\n## GEO visibility`);
      lines.push(mentionRate === null ? "No GEO checks recorded yet." : `Overall mention rate: ${mentionRate}% (${mentions.length - notMentioned.length}/${mentions.length} checks)`);
      if (notMentioned.length > 0) {
        lines.push("Not yet mentioned for:");
        for (const m of notMentioned.slice(0, 20)) {
          const competitors = (m.competitors_mentioned ?? []).join(", ") || "none named";
          lines.push(`- "${m.query}" (${m.provider}), competitors mentioned instead: ${competitors}`);
        }
      }
    }

    if (included.reddit) {
      lines.push(`\n## New Reddit opportunities (${newOpportunities.length})`);
      if (newOpportunities.length === 0) lines.push("None new.");
      for (const o of newOpportunities.slice(0, 20)) {
        lines.push(`- r/${o.subreddit}, matched "${o.matched_keyword}": ${o.thread_url}`);
      }
    }

    lines.push(
      `\n---\nWhen you're done, commit, push, and deploy on your own (this project auto-deploys on push to ` +
        `main) and confirm it's actually live before you finish, so I don't have to do anything manually.`
    );

    return lines.join("\n");
  }, [included, keywords, unpublishedArticles, openFindings, mentions, notMentioned, mentionRate, newOpportunities, site]);

  function toggle(key: SectionKey) {
    setIncluded((prev) => ({ ...prev, [key]: !prev[key] }));
  }

  function handleCopy() {
    navigator.clipboard.writeText(prompt);
    setCopyLabel("Copied!");
    setTimeout(() => setCopyLabel("Copy prompt"), 1500);
  }

  return (
    <div>
      <h1 className="mb-2 text-xl font-semibold">Claude Prompt</h1>
      <p className="mb-6 text-sm text-slate-500">
        Pick what to include, then paste the generated prompt into a fresh Claude Code session to keep
        working on this site from there.
      </p>

      <div className="mb-6 flex flex-wrap gap-4 rounded-lg border border-slate-200 bg-white p-4">
        {SECTIONS.map((s) => (
          <label key={s.key} className="flex items-center gap-2 text-sm text-slate-700">
            <input type="checkbox" checked={included[s.key]} onChange={() => toggle(s.key)} />
            {s.label}
          </label>
        ))}
      </div>

      <div className="mb-3 flex justify-end">
        <button
          onClick={handleCopy}
          className="rounded-md bg-brand-green px-4 py-2 text-sm font-semibold text-black"
        >
          {copyLabel}
        </button>
      </div>

      <pre className="max-h-[60vh] overflow-auto whitespace-pre-wrap rounded-lg border border-slate-200 bg-white p-5 text-sm text-slate-800">
        {prompt}
      </pre>
    </div>
  );
}
