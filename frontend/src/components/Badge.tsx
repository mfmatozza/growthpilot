const COLOR_BY_TONE: Record<string, string> = {
  neutral: "bg-slate-100 text-slate-700",
  positive: "bg-emerald-100 text-emerald-700",
  negative: "bg-rose-100 text-rose-700",
  warning: "bg-amber-100 text-amber-700",
};

interface BadgeProps {
  children: React.ReactNode;
  tone?: keyof typeof COLOR_BY_TONE;
}

export default function Badge({ children, tone = "neutral" }: BadgeProps) {
  return (
    <span className={`inline-block rounded-full px-2 py-0.5 text-xs font-medium ${COLOR_BY_TONE[tone]}`}>
      {children}
    </span>
  );
}
