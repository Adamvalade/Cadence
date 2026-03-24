"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { ExternalLink, Loader2 } from "lucide-react";
import StarRating from "@/components/StarRating";
import { api } from "@/lib/api";
import type { UserTrackRatingEntry } from "@/lib/types";

export default function UserRatedTracksSection({
  username,
  isOwnProfile,
}: {
  username: string;
  isOwnProfile: boolean;
}) {
  const [items, setItems] = useState<UserTrackRatingEntry[] | null>(null);

  useEffect(() => {
    let cancelled = false;
    api
      .get<UserTrackRatingEntry[]>(`/users/${username}/track-ratings`, { limit: "80" })
      .then((data) => {
        if (!cancelled) setItems(data);
      })
      .catch(() => {
        if (!cancelled) setItems([]);
      });
    return () => {
      cancelled = true;
    };
  }, [username]);

  if (items === null) {
    return (
      <div className="mt-8 flex items-center gap-2 text-sm text-muted-foreground">
        <Loader2 className="h-4 w-4 animate-spin" />
        Loading song ratings…
      </div>
    );
  }

  if (items.length === 0) {
    return null;
  }

  return (
    <div className="mt-8 rounded-lg border border-border bg-card p-3 sm:p-4">
      <h2 className="text-base font-semibold mb-3">Rated songs</h2>
      <p className="text-xs text-muted-foreground mb-3">
        {isOwnProfile
          ? "Tracks you’ve scored (newest updates first). Open an album to rate more."
          : `Tracks @${username} has scored on albums (newest updates first).`}
      </p>
      <ul className="h-72 sm:h-80 overflow-y-auto overscroll-contain space-y-2 text-sm pr-1">
        {items.map((t, i) => {
          const header = i === 0 || items[i - 1].album_id !== t.album_id;
          const spotifyUrl = `https://open.spotify.com/track/${t.spotify_track_id}`;
          return (
            <li key={`${t.album_id}-${t.track_id}`}>
              {header && (
                <Link
                  href={`/album/${t.album_id}`}
                  className="block text-xs font-medium text-muted-foreground hover:text-foreground mt-3 first:mt-0 mb-1"
                >
                  {t.album_title} <span className="font-normal">· {t.album_artist}</span>
                </Link>
              )}
              <div className="flex flex-wrap items-center justify-between gap-x-3 gap-y-1 pl-0 sm:pl-1 border-l-2 border-border/80 ml-0.5">
                <span className="text-foreground/95 min-w-0">
                  {t.disc_number > 1 ? `${t.disc_number}.` : ""}
                  {t.track_number}. {t.title}
                </span>
                <span className="flex shrink-0 items-center gap-2">
                  <StarRating value={t.rating} size="sm" readonly />
                  <a
                    href={spotifyUrl}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="inline-flex items-center gap-0.5 text-[10px] text-muted-foreground underline-offset-2 hover:underline"
                  >
                    Spotify <ExternalLink className="h-2.5 w-2.5" />
                  </a>
                </span>
              </div>
            </li>
          );
        })}
      </ul>
    </div>
  );
}
