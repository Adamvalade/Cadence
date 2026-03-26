"use client";

import { Star } from "lucide-react";
import { cn } from "@/lib/utils";
import { formatAverageRatingLabel, formatStoredRatingLabel, starScoreForDisplay } from "@/lib/ratingDisplay";

interface StarRatingProps {
  value: number;
  onChange?: (value: number) => void;
  size?: "sm" | "md" | "lg";
  readonly?: boolean;
}

const sizeMap = {
  sm: "h-4 w-4",
  md: "h-5 w-5",
  lg: "h-6 w-6",
};

function StarGlyph({
  starIndex1to5,
  score,
  sizeClass,
}: {
  starIndex1to5: number;
  score: number;
  sizeClass: string;
}) {
  const s = starIndex1to5;
  const filled = score >= s;
  const half = !filled && score >= s - 0.5;

  if (filled) {
    return <Star className={cn(sizeClass, "fill-yellow-400 text-yellow-400")} aria-hidden />;
  }
  if (half) {
    return (
      <span className="relative inline-block" aria-hidden>
        <Star className={cn(sizeClass, "text-muted-foreground/30")} />
        <span className="absolute inset-0 overflow-hidden w-1/2">
          <Star className={cn(sizeClass, "fill-yellow-400 text-yellow-400")} />
        </span>
      </span>
    );
  }
  return <Star className={cn(sizeClass, "text-muted-foreground/30")} aria-hidden />;
}

export default function StarRating({
  value,
  onChange,
  size = "md",
  readonly = false,
}: StarRatingProps) {
  const sizeClass = sizeMap[size];
  const drawScore = value > 0 ? starScoreForDisplay(value) : 0;

  if (readonly) {
    if (value <= 0) {
      return (
        <div className="flex items-center gap-0.5">
          {Array.from({ length: 5 }, (_, i) => (
            <Star key={i} className={cn(sizeClass, "text-muted-foreground/30")} aria-hidden />
          ))}
        </div>
      );
    }

    const label =
      Number.isInteger(value) && value >= 1 && value <= 10
        ? formatStoredRatingLabel(value)
        : formatAverageRatingLabel(value);

    return (
      <div className="flex items-center gap-0.5">
        {Array.from({ length: 5 }, (_, i) => (
          <StarGlyph key={i} starIndex1to5={i + 1} score={drawScore} sizeClass={sizeClass} />
        ))}
        <span className="ml-1.5 text-sm font-medium tabular-nums">{label}</span>
      </div>
    );
  }

  return (
    <div className="flex items-center gap-0.5">
      {Array.from({ length: 5 }, (_, i) => {
        const s = i + 1;
        const leftVal = 2 * s - 1;
        const rightVal = 2 * s;
        return (
          <span key={s} className={cn("relative inline-flex shrink-0 items-center justify-center", sizeClass)}>
            <button
              type="button"
              aria-label={`${s - 0.5} stars`}
              className="absolute left-0 top-0 z-10 h-full w-1/2 cursor-pointer rounded-l-sm focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary/50"
              onClick={() => onChange?.(leftVal)}
            />
            <button
              type="button"
              aria-label={`${s} stars`}
              className="absolute right-0 top-0 z-10 h-full w-1/2 cursor-pointer rounded-r-sm focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary/50"
              onClick={() => onChange?.(rightVal)}
            />
            <StarGlyph starIndex1to5={s} score={drawScore} sizeClass={sizeClass} />
          </span>
        );
      })}
      <span className="ml-2 text-sm font-medium tabular-nums text-muted-foreground">
        {value > 0 ? formatStoredRatingLabel(value) : "—"}
      </span>
    </div>
  );
}
