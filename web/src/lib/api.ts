import { readAccessToken } from "./sessionToken";

/**
 * When NEXT_PUBLIC_API_URL matches the site origin (e.g. both https://cadencemusik.com),
 * calling /auth/register would hit the Next.js page route instead of the API. Use the
 * server proxy in that case. Otherwise call the API host directly (e.g. api subdomain).
 */
function resolveApiBase(): string {
  if (typeof window === "undefined") {
    const internal = (process.env.API_URL || process.env.NEXT_PUBLIC_API_URL || "").trim();
    if (internal) return internal.replace(/\/$/, "");
    return "http://127.0.0.1:8000";
  }

  const configured = (process.env.NEXT_PUBLIC_API_URL || "").trim().replace(/\/$/, "");
  if (!configured) {
    return `${window.location.origin}/api/upstream`;
  }
  try {
    if (new URL(configured).origin === window.location.origin) {
      return `${window.location.origin}/api/upstream`;
    }
  } catch {
    return configured;
  }
  return configured;
}

export const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

type FetchOptions = RequestInit & { params?: Record<string, string> };

async function apiFetch<T>(path: string, options: FetchOptions = {}): Promise<T> {
  const { params, headers: customHeaders, ...restInit } = options;

  const base = resolveApiBase();
  let url = `${base}${path.startsWith("/") ? path : `/${path}`}`;
  if (params) {
    const searchParams = new URLSearchParams(params);
    url += `?${searchParams.toString()}`;
  }

  const bearer = readAccessToken();
  const res = await fetch(url, {
    ...restInit,
    credentials: "include",
    headers: {
      "Content-Type": "application/json",
      ...(bearer ? { Authorization: `Bearer ${bearer}` } : {}),
      ...(customHeaders as Record<string, string>),
    },
  });

  if (!res.ok) {
    const body = await res.json().catch(() => ({ detail: res.statusText }));
    const detail = body?.detail;
    const message =
      typeof detail === "string"
        ? detail
        : Array.isArray(detail)
          ? detail.map((d: { msg?: string }) => d?.msg).filter(Boolean).join(", ") || res.statusText
          : detail != null
            ? String(detail)
            : `API error ${res.status}`;
    throw new Error(message);
  }

  if (res.status === 204) return undefined as T;
  return res.json();
}

export const api = {
  get: <T>(path: string, params?: Record<string, string>) =>
    apiFetch<T>(path, { method: "GET", params }),

  post: <T>(path: string, body?: unknown) =>
    apiFetch<T>(path, { method: "POST", body: body ? JSON.stringify(body) : undefined }),

  put: <T>(path: string, body?: unknown) =>
    apiFetch<T>(path, { method: "PUT", body: body ? JSON.stringify(body) : undefined }),

  patch: <T>(path: string, body?: unknown) =>
    apiFetch<T>(path, { method: "PATCH", body: body ? JSON.stringify(body) : undefined }),

  delete: <T>(path: string) =>
    apiFetch<T>(path, { method: "DELETE" }),
};
