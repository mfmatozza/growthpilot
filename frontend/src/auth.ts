// Real check now: the token comes from POST /api/auth/login, verified
// server-side against ADMIN_EMAIL/ADMIN_PASSWORD (docs/DECISIONS.md #16).
// localStorage here is just where the browser keeps the token between
// visits — the actual gate is the backend rejecting bad/missing tokens.
const TOKEN_KEY = "gp_token";

export function getToken(): string | null {
  return localStorage.getItem(TOKEN_KEY);
}

export function isAuthed(): boolean {
  return getToken() !== null;
}

export function setToken(token: string): void {
  localStorage.setItem(TOKEN_KEY, token);
}

export function logOut(): void {
  localStorage.removeItem(TOKEN_KEY);
}
