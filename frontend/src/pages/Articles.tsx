import { useEffect, useState } from "react";

import { api, ApiError } from "../api/client";
import type { Article, ArticleType, Keyword } from "../api/types";
import Badge from "../components/Badge";
import { useSiteContext } from "../siteContext";

interface ArticleDetail extends Article {
  outline: { title: string; sections: { heading: string; key_points: string[] }[]; differentiation_angle: string } | null;
  body_markdown: string | null;
}

const ARTICLE_TYPES: { value: ArticleType; label: string }[] = [
  { value: "informational", label: "Informational" },
  { value: "how_to", label: "How-to" },
  { value: "comparison", label: "Comparison" },
];

export default function Articles() {
  const { siteId } = useSiteContext();
  const [articles, setArticles] = useState<Article[]>([]);
  const [approvedKeywords, setApprovedKeywords] = useState<Keyword[]>([]);
  const [selectedKeywordId, setSelectedKeywordId] = useState<string>("");
  const [articleType, setArticleType] = useState<ArticleType>("informational");
  const [generating, setGenerating] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [detail, setDetail] = useState<ArticleDetail | null>(null);
  const [copyLabel, setCopyLabel] = useState("Copy Markdown");

  const loadArticles = () => api.get<Article[]>(`/api/articles?site_id=${siteId}`).then(setArticles);
  const loadApprovedKeywords = () =>
    api.get<Keyword[]>(`/api/keywords?site_id=${siteId}&status=approved`).then(setApprovedKeywords);

  useEffect(() => {
    loadArticles();
    loadApprovedKeywords();
    setDetail(null);
  }, [siteId]);

  async function handleGenerate() {
    if (!selectedKeywordId) return;
    setGenerating(true);
    setError(null);
    try {
      const article = await api.post<ArticleDetail>("/api/articles/generate", {
        site_id: Number(siteId),
        keyword_id: Number(selectedKeywordId),
        article_type: articleType,
      });
      await loadArticles();
      setDetail(article);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : String(err));
    } finally {
      setGenerating(false);
    }
  }

  async function openDetail(id: number) {
    setError(null);
    try {
      const article = await api.get<ArticleDetail>(`/api/articles/${id}`);
      setDetail(article);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : String(err));
    }
  }

  async function updateStatus(status: Article["status"]) {
    if (!detail) return;
    const updated = await api.patch<Article>(`/api/articles/${detail.id}`, { status });
    setDetail({ ...detail, status: updated.status });
    await loadArticles();
  }

  function handleCopy() {
    if (!detail?.body_markdown) return;
    navigator.clipboard.writeText(detail.body_markdown);
    setCopyLabel("Copied!");
    setTimeout(() => setCopyLabel("Copy Markdown"), 1500);
  }

  if (detail) {
    return (
      <div>
        <button onClick={() => setDetail(null)} className="mb-4 text-sm text-slate-500 hover:text-slate-800">
          ← Back to articles
        </button>
        <div className="mb-4 flex items-center justify-between">
          <div>
            <h1 className="text-xl font-semibold">{detail.title}</h1>
            <div className="mt-1 flex items-center gap-2">
              <Badge>{detail.article_type}</Badge>
              <Badge tone={detail.status === "published" ? "positive" : "warning"}>{detail.status}</Badge>
            </div>
          </div>
          <div className="flex gap-2">
            <button
              onClick={handleCopy}
              className="rounded-md border border-slate-300 px-3 py-1.5 text-sm font-medium text-slate-700 hover:bg-slate-50"
            >
              {copyLabel}
            </button>
            {detail.status === "draft" && (
              <button
                onClick={() => updateStatus("review")}
                className="rounded-md border border-slate-300 px-3 py-1.5 text-sm font-medium text-slate-700 hover:bg-slate-50"
              >
                Mark for review
              </button>
            )}
            {detail.status === "review" && (
              <button
                onClick={() => updateStatus("published")}
                className="rounded-md bg-brand-green px-3 py-1.5 text-sm font-semibold text-black"
              >
                Mark published
              </button>
            )}
          </div>
        </div>
        {detail.outline?.differentiation_angle && (
          <p className="mb-4 text-sm text-slate-500">
            <span className="font-medium text-slate-600">Angle: </span>
            {detail.outline.differentiation_angle}
          </p>
        )}
        <pre className="max-h-[70vh] overflow-auto whitespace-pre-wrap rounded-lg border border-slate-200 bg-white p-5 text-sm text-slate-800">
          {detail.body_markdown}
        </pre>
      </div>
    );
  }

  return (
    <div>
      <h1 className="mb-2 text-xl font-semibold">Articles</h1>
      <p className="mb-6 text-sm text-slate-500">
        Semantic Markdown output, no images, no inline styling — drop it into any CMS. Nothing here ever
        auto-publishes anywhere; move it through draft → review → published yourself.
      </p>

      <div className="mb-6 flex flex-wrap items-end gap-3 rounded-lg border border-slate-200 bg-white p-4">
        <div className="min-w-[240px] flex-1">
          <label className="mb-1 block text-xs font-medium text-slate-500">Approved keyword</label>
          <select
            className="w-full rounded-md border border-slate-300 px-3 py-2 text-sm"
            value={selectedKeywordId}
            onChange={(e) => setSelectedKeywordId(e.target.value)}
          >
            <option value="">Select a keyword…</option>
            {approvedKeywords.map((k) => (
              <option key={k.id} value={k.id}>
                {k.keyword}
              </option>
            ))}
          </select>
        </div>
        <div>
          <label className="mb-1 block text-xs font-medium text-slate-500">Type</label>
          <select
            className="rounded-md border border-slate-300 px-3 py-2 text-sm"
            value={articleType}
            onChange={(e) => setArticleType(e.target.value as ArticleType)}
          >
            {ARTICLE_TYPES.map((t) => (
              <option key={t.value} value={t.value}>
                {t.label}
              </option>
            ))}
          </select>
        </div>
        <button
          className="rounded-md bg-brand-green px-4 py-2 text-sm font-semibold text-black disabled:opacity-50"
          onClick={handleGenerate}
          disabled={generating || !selectedKeywordId}
        >
          {generating ? "Generating… (can take a minute)" : "Generate article"}
        </button>
      </div>

      {approvedKeywords.length === 0 && (
        <div className="mb-6 rounded-md bg-brand-blueTint px-4 py-3 text-sm text-slate-600">
          No approved keywords yet — approve some on the Keywords tab first.
        </div>
      )}
      {error && <div className="mb-4 rounded-md bg-rose-50 px-4 py-3 text-sm text-rose-700">{error}</div>}

      <div className="overflow-hidden rounded-lg border border-slate-200 bg-white">
        <table className="w-full text-sm">
          <thead className="border-b border-slate-200 bg-slate-50 text-left text-xs uppercase text-slate-500">
            <tr>
              <th className="px-4 py-2">Title</th>
              <th className="px-4 py-2">Type</th>
              <th className="px-4 py-2">Status</th>
            </tr>
          </thead>
          <tbody>
            {articles.map((a) => (
              <tr
                key={a.id}
                className="cursor-pointer border-b border-slate-100 last:border-0 hover:bg-slate-50"
                onClick={() => openDetail(a.id)}
              >
                <td className="px-4 py-2 font-medium">{a.title}</td>
                <td className="px-4 py-2">{a.article_type}</td>
                <td className="px-4 py-2">
                  <Badge tone={a.status === "published" ? "positive" : "warning"}>{a.status}</Badge>
                </td>
              </tr>
            ))}
            {articles.length === 0 && (
              <tr>
                <td colSpan={3} className="px-4 py-8 text-center text-slate-400">
                  No articles yet.
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}
