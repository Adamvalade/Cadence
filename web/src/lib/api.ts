import { readAccessToken } from "./sessionToken";

export const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

const API_BASE = API_BASE_URL;

type FetchOptions = RequestInit & { params?: Record<string, string> };

async function apiFetch<T>(path: string, options: FetchOptions = {}): Promise<T> {
  const { params, headers: customHeaders, ...restInit } = options;

  let url = `${API_BASE}${path}`;
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
