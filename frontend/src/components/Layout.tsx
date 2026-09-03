import { NavLink, Outlet, useNavigate } from "react-router-dom";

import { logOut } from "../auth";

const NAV_ITEMS = [
  { to: "/dashboard", label: "Overview", end: true },
  { to: "/dashboard/keywords", label: "Keywords" },
  { to: "/dashboard/articles", label: "Articles" },
  { to: "/dashboard/audit", label: "Technical Audit" },
  { to: "/dashboard/geo", label: "GEO Tracker" },
  { to: "/dashboard/reddit", label: "Reddit Queue" },
];

export default function Layout() {
  const navigate = useNavigate();

  function handleLogOut() {
    logOut();
    navigate("/");
  }

  return (
    <div className="flex min-h-screen">
      <aside className="flex w-56 shrink-0 flex-col border-r border-slate-200 bg-white px-4 py-6">
        <div className="mb-8 px-2 text-lg font-semibold tracking-tight">GrowthPilot</div>
        <nav className="flex flex-1 flex-col gap-1">
          {NAV_ITEMS.map((item) => (
            <NavLink
              key={item.to}
              to={item.to}
              end={item.end}
              className={({ isActive }) =>
                `rounded-md px-3 py-2 text-sm font-medium transition-colors ${
                  isActive ? "bg-slate-900 text-white" : "text-slate-600 hover:bg-slate-100"
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
      <main className="flex-1 px-8 py-6">
        <Outlet />
      </main>
    </div>
  );
}
