"use client";

import { cn } from "@/lib/utils";

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
  const max = Math.max(1, ...entries.map((e) => e.count));

  return (
    <div className={cn("space-y-2", className)}>
      <p className="text-sm font-medium">Rating spread (album + song scores)</p>
      <div className="flex items-end gap-1 h-28">
        {entries.map(({ rating, count }) => (
          <div key={rating} className="flex-1 flex flex-col items-center gap-1 min-w-0">
            <div
              className="w-full rounded-t bg-primary/80 min-h-px transition-all"
              style={{ height: `${(count / max) * 100}%` }}
              title={`${rating}/10: ${count}`}
            />
            <span className="text-[10px] text-muted-foreground tabular-nums">{rating}</span>
          </div>
        ))}
      </div>
    </div>
  );
}
