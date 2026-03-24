const KEY = "cadence_access_token";

export function readAccessToken(): string | null {
  if (typeof window === "undefined") return null;
  return sessionStorage.getItem(KEY);
}

export function persistAccessToken(token: string | null): void {
  if (typeof window === "undefined") return;
  if (token) sessionStorage.setItem(KEY, token);
  else sessionStorage.removeItem(KEY);
}
