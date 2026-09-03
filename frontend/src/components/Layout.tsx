import { useEffect, useState } from "react";
import { Link, NavLink, Outlet, useNavigate, useParams } from "react-router-dom";

import { api } from "../api/client";
import type { Site } from "../api/types";
import { logOut } from "../auth";

export default function Layout() {
  const { siteId } = useParams<{ siteId: string }>();
  const navigate = useNavigate();
  const [site, setSite] = useState<Site | null>(null);

  useEffect(() => {
    if (siteId) api.get<Site>(`/api/sites/${siteId}`).then(setSite).catch(() => setSite(null));
  }, [siteId]);

  const navItems = [
    { to: `/dashboard/sites/${siteId}`, label: "Overview", end: true },
    { to: `/dashboard/sites/${siteId}/keywords`, label: "Keywords" },
    { to: `/dashboard/sites/${siteId}/articles`, label: "Articles" },
    { to: `/dashboard/sites/${siteId}/audit`, label: "Technical Audit" },
    { to: `/dashboard/sites/${siteId}/geo`, label: "GEO Tracker" },
    { to: `/dashboard/sites/${siteId}/reddit`, label: "Reddit Queue" },
  ];

  function handleLogOut() {
    logOut();
    navigate("/");
  }

  return (
    <div className="flex min-h-screen">
      <aside className="flex w-60 shrink-0 flex-col border-r border-slate-200 bg-white px-4 py-6">
        <Link to="/dashboard" className="mb-1 px-2 text-xs font-medium text-slate-400 hover:text-slate-700">
          ← All websites
        </Link>
        <div className="mb-6 px-2">
          <div className="truncate text-lg font-semibold tracking-tight">{site?.name ?? "…"}</div>
          {site && <div className="truncate text-xs text-slate-400">{site.url}</div>}
        </div>
        <nav className="flex flex-1 flex-col gap-1">
          {navItems.map((item) => (
            <NavLink
              key={item.to}
              to={item.to}
              end={item.end}
              className={({ isActive }) =>
                `rounded-md px-3 py-2 text-sm font-medium transition-colors ${
                  isActive ? "bg-brand-greenTint text-brand-green" : "text-slate-600 hover:bg-slate-100"
                }`
              }
            >
              {item.label}
            </NavLink>
          ))}
        </nav>
        <button onClick={handleLogOut} className="px-3 py-2 text-left text-sm font-medium text-slate-400 hover:text-slate-700">
          Log out
        </button>
      </aside>
      <main className="flex-1 bg-slate-50 px-8 py-6">
        <Outlet context={{ siteId: siteId!, site }} />
      </main>
    </div>
  );
}
