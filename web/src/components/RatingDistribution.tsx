"use client";

import { cn } from "@/lib/utils";
import { formatDistributionStepLabel } from "@/lib/ratingDisplay";

export default function RatingDistribution({
  distribution,
  className,
}: {
  distribution: Record<string, number>;
  className?: string;
}) {
  const entries = Array.from({ length: 10 }, (_, i) => {
    const k = String(i + 1);
    return { rating: i + 1, count: distribution[k] ?? 0 };
  });
  const total = entries.reduce((s, e) => s + e.count, 0);
  const max = Math.max(...entries.map((e) => e.count), 1);
  /** Pixel height — avoids broken % heights inside flex columns without a fixed track. */
  const maxBarPx = 80;

  return (
    <div className={cn("space-y-2", className)}>
      <p className="text-sm font-medium">Rating spread (album + song scores, out of 5★)</p>
      <div className="flex items-end justify-between gap-1 sm:gap-1.5 h-[5.5rem]">
        {entries.map(({ rating, count }) => {
          const h = Math.round((count / max) * maxBarPx);
          const barHeightPx = count === 0 ? 2 : Math.max(h, 4);
          return (
            <div
              key={rating}
              className="flex min-w-0 flex-1 flex-col items-center justify-end gap-1"
            >
              <div
                className="w-full max-w-[1.35rem] sm:max-w-none rounded-t bg-primary/85 transition-all"
                style={{ height: `${barHeightPx}px`, minHeight: count > 0 ? 4 : 2 }}
                title={`${formatDistributionStepLabel(rating)}★: ${count}`}
              />
              <span className="text-[10px] tabular-nums leading-none text-muted-foreground">
                {formatDistributionStepLabel(rating)}
              </span>
            </div>
          );
        })}
      </div>
      {total === 0 && (
        <p className="text-xs text-muted-foreground">No ratings yet — album and track scores will appear here.</p>
      )}
    </div>
  );
}
