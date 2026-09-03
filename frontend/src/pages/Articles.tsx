import { useEffect, useState } from "react";

import { api } from "../api/client";
import type { Article } from "../api/types";
import Badge from "../components/Badge";

export default function Articles() {
  const [articles, setArticles] = useState<Article[]>([]);

  useEffect(() => {
    api.get<Article[]>("/api/articles").then(setArticles);
  }, []);

  return (
    <div>
      <h1 className="mb-2 text-xl font-semibold">Articles</h1>
      <p className="mb-6 text-sm text-slate-500">
        Module 2 (generation pipeline) isn't built yet — approve keywords first, then this fills up.
      </p>
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
              <tr key={a.id} className="border-b border-slate-100 last:border-0">
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
