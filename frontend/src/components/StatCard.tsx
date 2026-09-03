import type { ReactNode } from "react";

interface StatCardProps {
  label: string;
  value: string | number;
  hint?: string;
  accent?: "green" | "blue";
  icon?: ReactNode;
}

const ACCENT_BG = { green: "bg-brand-greenTint text-brand-green", blue: "bg-brand-blueTint text-brand-blue" };

export default function StatCard({ label, value, hint, accent = "green", icon }: StatCardProps) {
  return (
    <div className="rounded-lg border border-slate-200 bg-white p-5">
      <div className="mb-3 flex items-center justify-between">
        <div className="text-xs font-medium uppercase tracking-wide text-slate-500">{label}</div>
        {icon && <div className={`flex h-7 w-7 items-center justify-center rounded-md ${ACCENT_BG[accent]}`}>{icon}</div>}
      </div>
      <div className="text-3xl font-semibold tracking-tight">{value}</div>
      {hint && <div className="mt-1 text-xs text-slate-400">{hint}</div>}
    </div>
  );
}
