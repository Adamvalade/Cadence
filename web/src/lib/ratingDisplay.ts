// API ratings are 1–10 (half-star steps); display as /5 via ÷2.

export function storedToStarScore(stored: number): number {
  return stored / 2;
}

export function starScoreForDisplay(stored: number): number {
  const raw = storedToStarScore(stored);
  return Math.min(5, Math.max(0, Math.round(raw * 2) / 2));
}

export function formatStoredRatingLabel(stored: number): string {
  const s = storedToStarScore(stored);
  const t = s % 1 === 0 ? String(s) : s.toFixed(1);
  return `${t}/5`;
}

export function formatAverageRatingLabel(avg: number): string {
  const s = avg / 2;
  const t = s.toFixed(1).replace(/\.0$/, "");
  return `${t}/5`;
}

export function formatDistributionStepLabel(step1to10: number): string {
  const s = step1to10 / 2;
  return s % 1 === 0 ? String(s) : s.toFixed(1);
}
