// Minimal inline stroke icons — no icon library needed for four glyphs.
const common = { width: 16, height: 16, viewBox: "0 0 24 24", fill: "none", stroke: "currentColor", strokeWidth: 2, strokeLinecap: "round" as const, strokeLinejoin: "round" as const };

export function TagIcon() {
  return (
    <svg {...common}>
      <path d="M12 2H2v10l10 10 10-10L12 2Z" />
      <circle cx="7" cy="7" r="1" fill="currentColor" />
    </svg>
  );
}

export function DocumentIcon() {
  return (
    <svg {...common}>
      <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8Z" />
      <path d="M14 2v6h6" />
    </svg>
  );
}

export function ShieldIcon() {
  return (
    <svg {...common}>
      <path d="M12 2 4 5v6c0 5 3.5 8.5 8 11 4.5-2.5 8-6 8-11V5l-8-3Z" />
    </svg>
  );
}

export function GlobeIcon() {
  return (
    <svg {...common}>
      <circle cx="12" cy="12" r="10" />
      <path d="M2 12h20M12 2a15 15 0 0 1 0 20 15 15 0 0 1 0-20Z" />
    </svg>
  );
}
