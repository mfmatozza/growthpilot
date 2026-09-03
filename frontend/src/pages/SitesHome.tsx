import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";

import { api, ApiError } from "../api/client";
import type { Site } from "../api/types";
import { logOut } from "../auth";

export default function SitesHome() {
  const navigate = useNavigate();
  const [sites, setSites] = useState<Site[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [name, setName] = useState("");
  const [url, setUrl] = useState("");
  const [creating, setCreating] = useState(false);

  useEffect(() => {
    api
      .get<Site[]>("/api/sites")
      .then(setSites)
      .catch((err) => setError(err instanceof ApiError ? err.message : String(err)))
      .finally(() => setLoading(false));
  }, []);

  async function handleAddSite(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    setCreating(true);
    try {
      const site = await api.post<Site>("/api/sites", { url, name });
      navigate(`/dashboard/sites/${site.id}`);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : String(err));
    } finally {
      setCreating(false);
    }
  }

  function handleLogOut() {
    logOut();
    navigate("/");
  }

  return (
    <div className="min-h-screen bg-slate-50 px-6 py-10 md:px-12">
      <div className="mx-auto max-w-4xl">
        <div className="mb-10 flex items-center justify-between">
          <h1 className="text-xl font-semibold tracking-tight">GrowthPilot</h1>
          <button onClick={handleLogOut} className="text-sm font-medium text-slate-400 hover:text-slate-700">
            Log out
          </button>
        </div>

        <form
          onSubmit={handleAddSite}
          className="mb-10 flex flex-wrap items-end gap-3 rounded-lg border border-slate-200 bg-white p-5"
        >
          <div className="min-w-[160px] flex-1">
            <label className="mb-1 block text-xs font-medium text-slate-500">Site name</label>
            <input
              className="w-full rounded-md border border-slate-300 px-3 py-2 text-sm"
              value={name}
              onChange={(e) => setName(e.target.value)}
              placeholder="Acme Co"
              required
            />
          </div>
          <div className="min-w-[220px] flex-1">
            <label className="mb-1 block text-xs font-medium text-slate-500">Website URL</label>
            <input
              className="w-full rounded-md border border-slate-300 px-3 py-2 text-sm"
              value={url}
              onChange={(e) => setUrl(e.target.value)}
              placeholder="https://acme.com"
              type="url"
              required
            />
          </div>
          <button
            type="submit"
            disabled={creating}
            className="rounded-md bg-brand-green px-5 py-2 text-sm font-semibold text-black disabled:opacity-50"
          >
            {creating ? "Adding…" : "Add website"}
          </button>
        </form>

        {error && <div className="mb-6 rounded-md bg-rose-50 px-4 py-3 text-sm text-rose-700">{error}</div>}

        {loading ? (
          <p className="text-sm text-slate-400">Loading sites…</p>
        ) : sites.length === 0 ? (
          <div className="rounded-lg border border-dashed border-slate-300 p-10 text-center text-sm text-slate-400">
            No websites yet — add one above to start tracking its SEO and GEO visibility.
          </div>
        ) : (
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
            {sites.map((site) => (
              <button
                key={site.id}
                onClick={() => navigate(`/dashboard/sites/${site.id}`)}
                className="rounded-lg border border-slate-200 bg-white p-5 text-left hover:border-brand-green hover:shadow-sm"
              >
                <div className="text-base font-semibold">{site.name}</div>
                <div className="mt-1 truncate text-sm text-slate-500">{site.url}</div>
                <div className="mt-4 text-xs font-medium text-brand-green">Open dashboard →</div>
              </button>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
