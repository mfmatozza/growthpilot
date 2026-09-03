import { useState } from "react";
import { useNavigate } from "react-router-dom";

import { logIn } from "../auth";

export default function Login() {
  const navigate = useNavigate();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    // No checks, on purpose — see src/auth.ts.
    logIn();
    navigate("/dashboard");
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
        />

        <label className="mb-1 block text-xs font-medium uppercase tracking-wide text-neutral-500">
          Password
        </label>
        <input
          type="password"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          className="mb-8 w-full border border-black px-3 py-2 text-sm outline-none"
          placeholder="••••••••"
        />

        <button type="submit" className="w-full border border-black bg-black py-3 text-sm font-semibold text-white hover:bg-white hover:text-black">
          Continue
        </button>
      </form>
    </div>
  );
}
