"use client";

import { useCallback, useEffect, useState } from "react";
import { Loader2 } from "lucide-react";
import StarRating from "@/components/StarRating";
import { Button } from "@/components/ui/button";
import { api } from "@/lib/api";
import type { AlbumTrackRow, AlbumTracksPayload } from "@/lib/types";

function recomputeSummary(tracks: AlbumTracksPayload["tracks"]): Pick<AlbumTracksPayload, "my_rated_count" | "my_track_average"> {
  const rated = tracks.filter((t) => t.my_rating != null).map((t) => t.my_rating as number);
  return {
    my_rated_count: rated.length,
    my_track_average: rated.length ? Math.round((rated.reduce((a, b) => a + b, 0) / rated.length) * 10) / 10 : null,
  };
}

export default function AlbumTrackRatings({
  albumId,
  hasSpotify,
  canRate,
}: {
  albumId: string;
  hasSpotify: boolean;
  canRate: boolean;
}) {
  const [data, setData] = useState<AlbumTracksPayload | null>(null);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [savingTrackId, setSavingTrackId] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(
    async (opts?: { refresh?: boolean }) => {
      const isRefresh = Boolean(opts?.refresh);
      if (isRefresh) setRefreshing(true);
      else setLoading(true);
      setError(null);
      try {
        const params = isRefresh ? { refresh: "true" } : undefined;
        const payload = await api.get<AlbumTracksPayload>(`/albums/${albumId}/tracks`, params);
        setData(payload);
      } catch {
        setError("Could not load tracks.");
        setData(null);
      } finally {
        setLoading(false);
        setRefreshing(false);
      }
    },
    [albumId]
  );

  useEffect(() => {
    load();
  }, [load]);

  const onRate = async (trackId: string, rating: number) => {
    if (!canRate || rating < 1) return;
    setSavingTrackId(trackId);
    setError(null);
    try {
      const updated = await api.put<AlbumTrackRow>(`/albums/${albumId}/tracks/${trackId}/rating`, { rating });
      setData((prev) => {
        if (!prev) return prev;
        const tracks = prev.tracks.map((t) =>
          t.id === trackId
            ? { ...t, my_rating: updated.my_rating }
            : t
        );
        const { my_rated_count, my_track_average } = recomputeSummary(tracks);
        return { ...prev, tracks, my_rated_count, my_track_average };
      });
    } catch (e) {
      setError(e instanceof Error ? e.message : "Could not save rating.");
    } finally {
      setSavingTrackId(null);
    }
  };

  if (!hasSpotify) {
    return (
      <div className="rounded-lg border border-border bg-muted/30 px-4 py-3 text-sm text-muted-foreground">
        Track lists and per-song ratings are available for albums imported from Spotify.
      </div>
    );
  }

  if (loading) {
    return (
      <div className="flex items-center gap-2 text-muted-foreground text-sm py-4">
        <Loader2 className="h-4 w-4 animate-spin" />
        Loading tracks…
      </div>
    );
  }

  if (error && !data) {
    return (
      <div className="space-y-3">
        <h2 className="text-xl font-semibold">Tracks</h2>
        <p className="text-sm text-destructive" role="alert">
          {error}
        </p>
        <Button type="button" variant="outline" size="sm" disabled={refreshing} onClick={() => load({ refresh: true })}>
          {refreshing ? <Loader2 className="h-4 w-4 animate-spin" /> : "Try again from Spotify"}
        </Button>
      </div>
    );
  }

  if (!data || data.track_count === 0) {
    return (
      <div className="space-y-3 rounded-xl border border-border bg-card p-4">
        <div>
          <h2 className="text-xl font-semibold">Tracks</h2>
          <p className="text-sm text-muted-foreground mt-1">
            No songs loaded for this album yet. This can happen after a sync glitch—reload from Spotify.
          </p>
          {!canRate && (
            <p className="text-sm text-muted-foreground mt-2">Sign in to rate tracks once they appear.</p>
          )}
        </div>
        <Button type="button" variant="outline" size="sm" disabled={refreshing} onClick={() => load({ refresh: true })}>
          {refreshing ? <Loader2 className="h-4 w-4 animate-spin" /> : "Reload tracks from Spotify"}
        </Button>
      </div>
    );
  }

  let lastDisc: number | null = null;

  return (
    <div className="space-y-3 rounded-xl border border-border bg-card p-4">
      <div className="flex flex-col sm:flex-row sm:items-end sm:justify-between gap-2">
        <div>
          <h2 className="text-xl font-semibold">Tracks</h2>
          <p className="text-sm text-muted-foreground mt-1">
            Rate songs 1–10. Your album review is separate and still drives the feed.
          </p>
          {!canRate && (
            <p className="text-sm text-muted-foreground mt-2">Sign in to rate individual tracks.</p>
          )}
        </div>
        <div className="flex flex-col items-start sm:items-end gap-2">
          {canRate && data.my_rated_count > 0 && data.my_track_average != null && (
            <p className="text-sm text-muted-foreground tabular-nums">
              Your song average: <span className="font-medium text-foreground">{data.my_track_average}</span>
              <span className="text-muted-foreground"> / 10</span>
              <span className="text-muted-foreground"> ({data.my_rated_count}/{data.track_count} rated)</span>
            </p>
          )}
          <Button
            type="button"
            variant="ghost"
            size="sm"
            className="text-xs h-8"
            disabled={refreshing}
            title="Re-downloads tracks from Spotify and clears your per-song ratings for this album."
            onClick={() => load({ refresh: true })}
          >
            {refreshing ? <Loader2 className="h-3 w-3 animate-spin" /> : "Re-sync from Spotify"}
          </Button>
        </div>
      </div>

      {error && (
        <p className="text-sm text-destructive" role="alert">
          {error}
        </p>
      )}

      <ul className="rounded-lg border border-border divide-y max-h-[28rem] overflow-y-auto">
        {data.tracks.map((track) => {
          const showDisc = lastDisc !== track.disc_number;
          lastDisc = track.disc_number;
          return (
            <li key={track.id}>
              {showDisc && track.disc_number > 1 && (
                <div className="px-3 py-2 text-xs font-medium text-muted-foreground bg-muted/40">
                  Disc {track.disc_number}
                </div>
              )}
              <div className="flex flex-col sm:flex-row sm:items-center gap-2 px-3 py-2.5 hover:bg-muted/20">
                <div className="flex items-start gap-2 min-w-0 flex-1">
                  <span className="text-muted-foreground tabular-nums text-sm w-8 shrink-0 pt-0.5">
                    {track.track_number}
                  </span>
                  <span className="text-sm font-medium leading-snug break-words">{track.title}</span>
                </div>
                <div className="shrink-0 sm:pl-2">
                  {canRate ? (
                    <div className="flex items-center gap-2">
                      {savingTrackId === track.id && (
                        <Loader2 className="h-4 w-4 animate-spin text-muted-foreground" aria-hidden />
                      )}
                      <StarRating
                        value={track.my_rating ?? 0}
                        onChange={(v) => onRate(track.id, v)}
                        size="sm"
                      />
                    </div>
                  ) : track.my_rating != null ? (
                    <StarRating value={track.my_rating} size="sm" readonly />
                  ) : (
                    <span className="text-xs text-muted-foreground">—</span>
                  )}
                </div>
              </div>
            </li>
          );
        })}
      </ul>
    </div>
  );
}
