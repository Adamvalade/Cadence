const STORAGE_KEY = "cadence_recent_searches";
const MAX = 10;

function parseList(raw: string | null): string[] {
  if (!raw) return [];
  try {
    const v = JSON.parse(raw) as unknown;
    if (!Array.isArray(v)) return [];
    return v.filter((x): x is string => typeof x === "string" && x.trim().length > 0);
  } catch {
    return [];
  }
}

export function readRecentSearches(): string[] {
  if (typeof window === "undefined") return [];
  return parseList(localStorage.getItem(STORAGE_KEY));
}

export function pushRecentSearch(query: string): void {
  const t = query.trim();
  if (!t || typeof window === "undefined") return;
  const lower = t.toLowerCase();
  const list = readRecentSearches().filter((x) => x.toLowerCase() !== lower);
  list.unshift(t);
  localStorage.setItem(STORAGE_KEY, JSON.stringify(list.slice(0, MAX)));
}

export function clearRecentSearches(): void {
  if (typeof window === "undefined") return;
  localStorage.removeItem(STORAGE_KEY);
}
