import { Link } from "react-router-dom";

import RotatingWord from "../components/RotatingWord";

const HOOK_WORDS = ["smarter", "faster", "everywhere", "automatically", "while you sleep"];

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
              className="mt-10 inline-block border border-black bg-black px-8 py-3 text-sm font-semibold text-white hover:bg-white hover:text-black"
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

      <section className="border-t border-black px-6 py-24 md:px-12">
        <h2 className="max-w-3xl text-3xl font-bold leading-snug md:text-5xl">
          Stop paying a subscription to rank. Start owning the pipeline.
        </h2>
        <Link
          to="/login"
          className="mt-10 inline-block border border-black bg-black px-8 py-3 text-sm font-semibold text-white hover:bg-white hover:text-black"
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
