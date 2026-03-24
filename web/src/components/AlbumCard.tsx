"use client";

import Image from "next/image";
import Link from "next/link";
import { Card } from "@/components/ui/card";
import { Music } from "lucide-react";

interface AlbumCardProps {
  id: string;
  title: string;
  artist: string;
  coverUrl: string | null;
  rating?: number | null;
  reviewCount?: number;
}

export default function AlbumCard({ id, title, artist, coverUrl, rating, reviewCount }: AlbumCardProps) {
  return (
    <Link href={`/album/${id}`}>
      <Card className="group gap-0 overflow-hidden border-border/50 pt-0 transition-all hover:border-primary/25 hover:ring-1 hover:ring-primary/15">
        <div className="aspect-square relative bg-muted">
          {coverUrl ? (
            <Image
              src={coverUrl}
              alt={title}
              fill
              className="object-cover group-hover:scale-105 transition-transform duration-300"
              sizes="(max-width: 768px) 50vw, 200px"
            />
          ) : (
            <div className="w-full h-full flex items-center justify-center">
              <Music className="h-12 w-12 text-muted-foreground/40" />
            </div>
          )}
        </div>
        <div className="p-3 space-y-1">
          <h3 className="font-medium text-sm leading-tight line-clamp-1">{title}</h3>
          <p className="text-xs text-muted-foreground line-clamp-1">{artist}</p>
          {(rating != null || reviewCount != null) && (
            <div className="flex items-center gap-2 text-xs text-muted-foreground">
              {rating != null && <span className="font-medium">{rating.toFixed(1)}/10</span>}
              {reviewCount != null && reviewCount > 0 && (
                <span>{reviewCount} {reviewCount === 1 ? "review" : "reviews"}</span>
              )}
            </div>
          )}
        </div>
      </Card>
    </Link>
  );
}
