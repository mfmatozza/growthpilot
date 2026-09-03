import { Link } from "react-router-dom";

import RotatingWord from "../components/RotatingWord";

const HOOK_WORDS = ["smarter", "faster", "everywhere", "automatically", "while you sleep"];

const FEATURES = [
  {
    title: "Keyword research",
    accent: "green" as const,
    body: "Crawls your site, profiles your business, and generates 30-50 scored keyword opportunities — you approve what's worth writing.",
  },
  {
    title: "Content generation",
    accent: "blue" as const,
    body: "Outlines, drafts, internal links, and fact-checks articles section by section, with a comparison-post mode for buyer's-guide content.",
  },
  {
    title: "Technical audits",
    accent: "green" as const,
    body: "Weekly Lighthouse + crawl checks translated into a plain-English, severity-ranked list — not raw JSON you have to interpret.",
  },
  {
    title: "GEO visibility",
    accent: "blue" as const,
    body: "Tracks whether ChatGPT, Claude, Gemini, and Perplexity mention your brand for the queries that matter, and who they mention instead.",
  },
  {
    title: "Reddit monitoring",
    accent: "green" as const,
    body: "Surfaces relevant threads with a drafted reply — always reviewed by a human before anything is posted.",
  },
  {
    title: "One login, every site",
    accent: "blue" as const,
    body: "Add a website and it gets its own dashboard — keywords, content, audits, and GEO tracking scoped per site, not lumped together.",
  },
];

export default function Landing() {
  return (
    <div className="bg-white text-black">
      <header className="flex items-center justify-between border-b border-black px-6 py-5 md:px-12">
        <span className="text-sm font-semibold tracking-tight">GROWTHPILOT</span>
        <Link to="/login" className="border border-black px-4 py-1.5 text-sm font-medium hover:bg-black hover:text-white">
          Log in
        </Link>
      </header>

      <section className="flex min-h-[calc(100vh-65px)] flex-col justify-between px-6 md:px-12">
        <div className="flex flex-1 flex-col justify-center py-16">
          <h1 className="max-w-4xl text-5xl font-bold leading-tight tracking-tight md:text-7xl">
            Get found <RotatingWord words={HOOK_WORDS} />.
          </h1>
          <p className="mt-6 max-w-xl text-lg text-neutral-600">
            Keyword research, content, technical audits, and AI-search visibility — one tool, run on your
            own infrastructure, billed by the API call instead of the seat.
          </p>
          <div>
            <Link
              to="/login"
              className="mt-10 inline-block border border-black bg-brand-green px-8 py-3 text-sm font-semibold text-black hover:bg-black hover:text-brand-green"
            >
              Get started
            </Link>
          </div>
        </div>

        <button
          onClick={() => window.scrollTo({ top: window.innerHeight, behavior: "smooth" })}
          className="mb-8 flex items-center gap-2 self-start text-xs font-medium uppercase tracking-widest text-neutral-500 hover:text-black"
        >
          Scroll
          <span aria-hidden className="animate-bounce">
            ↓
          </span>
        </button>
      </section>

      <section className="border-t border-black px-6 py-20 md:px-12">
        <h2 className="mb-2 text-sm font-semibold uppercase tracking-widest text-neutral-500">What it does</h2>
        <p className="mb-12 max-w-2xl text-2xl font-bold leading-snug md:text-3xl">
          Five pipelines that usually cost five subscriptions, replaced with one tool that only charges you
          for the API calls it actually makes.
        </p>
        <div className="grid grid-cols-1 gap-px border border-black bg-black sm:grid-cols-2 lg:grid-cols-3">
          {FEATURES.map((f) => (
            <div key={f.title} className="bg-white p-6">
              <div className={`mb-4 h-1.5 w-10 ${f.accent === "green" ? "bg-brand-green" : "bg-brand-blue"}`} />
              <h3 className="mb-2 text-lg font-bold">{f.title}</h3>
              <p className="text-sm text-neutral-600">{f.body}</p>
            </div>
          ))}
        </div>
      </section>

      <section className="border-t border-black bg-brand-greenTint px-6 py-20 md:px-12">
        <div className="grid grid-cols-1 gap-10 md:grid-cols-2">
          <div>
            <h2 className="mb-2 text-sm font-semibold uppercase tracking-widest text-neutral-500">The old way</h2>
            <p className="text-xl font-bold leading-snug">
              $200-500/mo for an AI-SEO SaaS, whether you use it once or every day, plus separate tools for
              audits and AI-search tracking.
            </p>
          </div>
          <div>
            <h2 className="mb-2 text-sm font-semibold uppercase tracking-widest text-brand-green">GrowthPilot</h2>
            <p className="text-xl font-bold leading-snug">
              Self-hosted. You own the code and the data. You only pay OpenAI, DataForSEO, and the other
              APIs for what you actually run — nothing when you don't.
            </p>
          </div>
        </div>
      </section>

      <section className="border-t border-black px-6 py-24 md:px-12">
        <h2 className="max-w-3xl text-3xl font-bold leading-snug md:text-5xl">
          Stop paying a subscription to rank. Start owning the pipeline.
        </h2>
        <Link
          to="/login"
          className="mt-10 inline-block border border-black bg-brand-blue px-8 py-3 text-sm font-semibold text-black hover:bg-black hover:text-brand-blue"
        >
          Start now
        </Link>
      </section>

      <footer className="flex flex-col gap-2 border-t border-black px-6 py-8 text-xs text-neutral-500 md:flex-row md:items-center md:justify-between md:px-12">
        <span>© {new Date().getFullYear()} GrowthPilot</span>
        <span>Self-hosted. Usage-based. Yours.</span>
      </footer>
    </div>
  );
}
