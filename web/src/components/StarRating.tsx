"use client";

import { Star } from "lucide-react";
import { cn } from "@/lib/utils";

interface StarRatingProps {
  value: number;
  onChange?: (value: number) => void;
  max?: number;
  size?: "sm" | "md" | "lg";
  readonly?: boolean;
}

const sizeMap = {
  sm: "h-4 w-4",
  md: "h-5 w-5",
  lg: "h-6 w-6",
};

export default function StarRating({
  value,
  onChange,
  max = 10,
  size = "md",
  readonly = false,
}: StarRatingProps) {
  const fullStars = Math.floor(value / 2);
  const hasHalf = value % 2 === 1;
  const totalStars = max / 2;

  if (readonly) {
    return (
      <div className="flex items-center gap-0.5">
        {Array.from({ length: totalStars }, (_, i) => (
          <Star
            key={i}
            className={cn(
              sizeMap[size],
              i < fullStars
                ? "fill-yellow-400 text-yellow-400"
                : i === fullStars && hasHalf
                  ? "fill-yellow-400/50 text-yellow-400"
                  : "text-muted-foreground/30"
            )}
          />
        ))}
        <span className="ml-1.5 text-sm font-medium tabular-nums">{value}/{max}</span>
      </div>
    );
  }

  return (
    <div className="flex items-center gap-1">
      {Array.from({ length: max }, (_, i) => {
        const ratingValue = i + 1;
        const starIndex = Math.floor(i / 2);
        const isSecondHalf = i % 2 === 1;

        return (
          <button
            key={i}
            type="button"
            onClick={() => onChange?.(ratingValue)}
            className={cn(
              "transition-colors",
              ratingValue <= value
                ? "text-yellow-400"
                : "text-muted-foreground/30 hover:text-yellow-400/50"
            )}
          >
            {isSecondHalf ? (
              <Star className={cn(sizeMap[size], ratingValue <= value && "fill-current")} />
            ) : (
              <div className="relative">
                <Star className={cn(sizeMap[size], ratingValue <= value && "fill-current")} />
              </div>
            )}
          </button>
        );
      })}
      <span className="ml-2 text-sm font-medium tabular-nums text-muted-foreground">
        {value}/{max}
      </span>
    </div>
  );
}
