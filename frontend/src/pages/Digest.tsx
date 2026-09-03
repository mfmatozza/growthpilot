import { useEffect, useMemo, useState } from "react";

import { api } from "../api/client";
import type { Article, AuditFinding, GeoMention, Keyword } from "../api/types";
import { useSiteContext } from "../siteContext";

// No Reddit section: that feature is hidden from the UI entirely right now
// (Reddit closed self-service API registration — see docs/DECISIONS.md #29),
// so reddit_opportunities is always empty and a checkbox for it would be dead weight.
type SectionKey = "keywords" | "articles" | "audit" | "geo";

const SECTIONS: { key: SectionKey; label: string }[] = [
  { key: "keywords", label: "Keywords awaiting review" },
  { key: "articles", label: "Draft/review articles" },
  { key: "audit", label: "Open technical issues" },
  { key: "geo", label: "GEO visibility gaps" },
];

// Full article bodies get embedded (not just title/status) so a fresh
// session actually has content to place into the site, not just a pointer
// — see docs/DECISIONS.md #30. Capped because embedding many full drafts
// makes for an enormous prompt.
const MAX_ARTICLE_BODIES_TO_EMBED = 3;

interface ArticleDetail extends Article {
  body_markdown: string | null;
}

export default function Digest() {
  const { siteId, site } = useSiteContext();
  const [included, setIncluded] = useState<Record<SectionKey, boolean>>({
    keywords: true,
    articles: true,
    audit: true,
    geo: true,
  });
  const [keywords, setKeywords] = useState<Keyword[]>([]);
  const [articles, setArticles] = useState<Article[]>([]);
  const [articleBodies, setArticleBodies] = useState<Record<number, string>>({});
  const [findings, setFindings] = useState<AuditFinding[]>([]);
  const [mentions, setMentions] = useState<GeoMention[]>([]);
  const [copyLabel, setCopyLabel] = useState("Copy prompt");

  useEffect(() => {
    api.get<Keyword[]>(`/api/keywords?site_id=${siteId}&status=candidate`).then(setKeywords);
    api.get<Article[]>(`/api/articles?site_id=${siteId}`).then(setArticles);
    api.get<AuditFinding[]>(`/api/audit-findings?site_id=${siteId}`).then(setFindings);
    api.get<GeoMention[]>(`/api/geo-mentions?site_id=${siteId}`).then(setMentions);
  }, [siteId]);

  const unpublishedArticles = articles.filter((a) => a.status !== "published");

  useEffect(() => {
    const toFetch = unpublishedArticles.slice(0, MAX_ARTICLE_BODIES_TO_EMBED);
    toFetch.forEach((a) => {
      if (a.id in articleBodies) return;
      api.get<ArticleDetail>(`/api/articles/${a.id}`).then((detail) => {
        setArticleBodies((prev) => ({ ...prev, [a.id]: detail.body_markdown ?? "" }));
      });
    });
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [articles]);

  const openFindings = findings.filter((f) => !f.resolved_at);
  const notMentioned = mentions.filter((m) => !m.mentioned);
  const mentionRate = mentions.length ? Math.round(((mentions.length - notMentioned.length) / mentions.length) * 100) : null;

  const prompt = useMemo(() => {
    const lines: string[] = [
      `You're continuing SEO/GEO work for ${site?.name ?? "this site"} (${site?.url ?? ""}). This session's ` +
        `working directory should be that site's own codebase, not the GrowthPilot tool that produced this data.`,
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

      const embedded = unpublishedArticles.slice(0, MAX_ARTICLE_BODIES_TO_EMBED);
      const pointerOnly = unpublishedArticles.slice(MAX_ARTICLE_BODIES_TO_EMBED);

      for (const a of embedded) {
        lines.push(`\n### "${a.title}" (${a.status}, ${a.article_type}) — publish at slug: ${a.slug}`);
        const body = articleBodies[a.id];
        lines.push(body === undefined ? "(loading content…)" : body || "(empty draft)");
      }
      for (const a of pointerOnly) {
        lines.push(`- "${a.title}" (${a.status}, ${a.article_type}), /${a.slug} — full body not embedded here, fetch it from GrowthPilot's GET /api/articles/${a.id} before publishing.`);
      }

      if (embedded.length > 0) {
        lines.push(
          `\n### Publishing checklist for the article(s) above (SEO/indexing)\n` +
            `- Use each article's exact slug as the URL path segment, unchanged.\n` +
            `- Set the page <title> to the article's title (or a compelling variant under 60 characters) and write a meta description under 160 characters summarizing it.\n` +
            `- Add a canonical <link rel="canonical"> tag pointing at the final public URL for that page.\n` +
            `- Add Open Graph and Twitter Card meta tags (og:title, og:description, og:url, og:type=article, twitter:card=summary_large_image).\n` +
            `- Preserve the Markdown's heading hierarchy exactly as written (one H1, then H2s for each section) — don't flatten, reorder, or add headings that aren't there.\n` +
            `- Add Article/BlogPosting JSON-LD structured data (headline, datePublished, author, publisher) if this site's stack supports structured data.\n` +
            `- Resolve every [VERIFY] tag in the draft (confirm the claim is accurate or remove it) before publishing — never ship one as-is.\n` +
            `- Keep the Markdown's internal links intact when converting to this site's format.\n` +
            `- Add the new URL(s) to this site's sitemap.xml (or trigger its framework's sitemap regeneration) and confirm robots.txt doesn't disallow the path.\n` +
            `- Google deprecated the sitemap ping endpoint in 2023 — don't try to ping it. After deploying, tell me to request indexing manually via Google Search Console's URL Inspection tool for each new URL.`
        );
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

    lines.push(
      `\n---\nBefore you finish: update the sitemap with any newly published URLs, verify the robots.txt ` +
        `allows them, and remind me to request indexing for each one in Google Search Console (there's no ` +
        `automatic ping anymore). Then commit, push, and deploy on your own (this project auto-deploys on ` +
        `push to main) and confirm it's actually live, so I don't have to do anything manually.`
    );

    return lines.join("\n");
  }, [included, keywords, unpublishedArticles, articleBodies, openFindings, mentions, notMentioned, mentionRate, site]);

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
        Pick what to include, then paste the generated prompt into a fresh Claude Code session — running in
        your actual website's repo, not this one — to publish and keep working from there.
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
