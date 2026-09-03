import { useState } from "react";
import { useNavigate } from "react-router-dom";

import { setToken } from "../auth";

const API_BASE = import.meta.env.VITE_API_BASE_URL ?? "";

export default function Login() {
  const navigate = useNavigate();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    setSubmitting(true);
    try {
      // Deliberately not routed through api/client.ts — that client's 401
      // handling assumes an already-authenticated session and would redirect
      // instead of letting this page show "wrong credentials".
      const response = await fetch(`${API_BASE}/api/auth/login`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email, password }),
      });
      if (!response.ok) {
        setError(response.status === 401 ? "Wrong email or password." : "Login failed. Try again.");
        return;
      }
      const { token } = await response.json();
      setToken(token);
      navigate("/dashboard");
    } catch {
      setError("Couldn't reach the server. Try again.");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div className="flex min-h-screen items-center justify-center bg-white px-6 text-black">
      <form onSubmit={handleSubmit} className="w-full max-w-sm">
        <h1 className="mb-8 text-2xl font-bold tracking-tight">Log in</h1>

        <label className="mb-1 block text-xs font-medium uppercase tracking-wide text-neutral-500">
          Email
        </label>
        <input
          type="email"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          className="mb-6 w-full border border-black px-3 py-2 text-sm outline-none"
          placeholder="you@company.com"
          required
        />

        <label className="mb-1 block text-xs font-medium uppercase tracking-wide text-neutral-500">
          Password
        </label>
        <input
          type="password"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          className="mb-4 w-full border border-black px-3 py-2 text-sm outline-none"
          placeholder="••••••••"
          required
        />

        {error && <p className="mb-4 text-sm text-red-600">{error}</p>}

        <button
          type="submit"
          disabled={submitting}
          className="w-full border border-brand-green bg-brand-green py-3 text-sm font-semibold text-black disabled:opacity-50"
        >
          {submitting ? "Checking…" : "Continue"}
        </button>
      </form>
    </div>
  );
}
