// Not real authentication — a client-side UX gate only, per project decision
// (docs/DECISIONS.md #13). Nothing here should be trusted as a security
// boundary; the backend still has no auth of its own (decision #7).
const AUTH_KEY = "gp_authed";

export function isAuthed(): boolean {
  return localStorage.getItem(AUTH_KEY) === "true";
}

export function logIn(): void {
  localStorage.setItem(AUTH_KEY, "true");
}

export function logOut(): void {
  localStorage.removeItem(AUTH_KEY);
}
