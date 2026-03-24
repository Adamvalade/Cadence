"use client";

import { useEffect, useState } from "react";
import Image from "next/image";
import { Loader2, Music, Search } from "lucide-react";
import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { api } from "@/lib/api";
import type { FeaturedTrackPublic, TrackSearchResult, UserProfile } from "@/lib/types";

const EMPTY: (FeaturedTrackPublic | null)[] = [null, null, null, null, null];

function slotsFromProfile(profile: UserProfile): (FeaturedTrackPublic | null)[] {
  const arr: (FeaturedTrackPublic | null)[] = [...EMPTY];
  for (const f of profile.featured_tracks) {
    if (f.slot >= 0 && f.slot < 5) arr[f.slot] = f;
  }
  return arr;
}

export default function FeaturedTracksEditor({
  profile,
  onSaved,
}: {
  profile: UserProfile;
  onSaved: (p: UserProfile) => void;
}) {
  const [open, setOpen] = useState(false);
  const [slots, setSlots] = useState<(FeaturedTrackPublic | null)[]>(() => slotsFromProfile(profile));
  const [pickingSlot, setPickingSlot] = useState<number | null>(null);
  const [q, setQ] = useState("");
  const [searching, setSearching] = useState(false);
  const [results, setResults] = useState<TrackSearchResult[]>([]);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (open) {
      setSlots(slotsFromProfile(profile));
      setPickingSlot(null);
      setQ("");
      setResults([]);
      setError(null);
    }
  }, [open, profile]);

  const runSearch = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!q.trim()) return;
    setSearching(true);
    setError(null);
    try {
      const rows = await api.get<TrackSearchResult[]>("/spotify/tracks/search", { q: q.trim() });
      setResults(rows);
    } catch {
      setError("Search failed.");
      setResults([]);
    } finally {
      setSearching(false);
    }
  };

  const pickTrack = (t: TrackSearchResult) => {
    if (pickingSlot === null) return;
    const f: FeaturedTrackPublic = {
      slot: pickingSlot,
      spotify_track_id: t.spotify_track_id,
      title: t.title,
      artist: t.artist,
      album_title: t.album_title,
      cover_image_url: t.cover_image_url,
      open_url: `https://open.spotify.com/track/${t.spotify_track_id}`,
    };
    setSlots((prev) => {
      const next = [...prev];
      next[pickingSlot] = f;
      return next;
    });
    setPickingSlot(null);
    setResults([]);
    setQ("");
  };

  const clearSlot = (i: number) => {
    setSlots((prev) => {
      const next = [...prev];
      next[i] = null;
      return next;
    });
  };

  const save = async () => {
    setSaving(true);
    setError(null);
    try {
      const payload = {
        slots: slots.map((s) => (s ? s.spotify_track_id : null)),
      };
      const updated = await api.put<UserProfile>("/users/me/featured-tracks", payload);
      onSaved(updated);
      setOpen(false);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Could not save.");
    } finally {
      setSaving(false);
    }
  };

  return (
    <>
      <Button variant="outline" size="sm" onClick={() => setOpen(true)}>
        Edit featured songs
      </Button>

      <Dialog open={open} onOpenChange={setOpen}>
        <DialogContent className="sm:max-w-md max-h-[min(90vh,32rem)] flex flex-col gap-0 p-0 overflow-hidden">
          <DialogHeader className="p-4 pb-2 shrink-0">
            <DialogTitle>Featured songs</DialogTitle>
            <DialogDescription>
              Pick up to 5 tracks to show on your profile (what you&apos;re replaying lately).
            </DialogDescription>
          </DialogHeader>

          <div className="px-4 flex-1 min-h-0 overflow-y-auto space-y-3 pb-2">
            {slots.map((s, i) => (
              <div
                key={i}
                className="rounded-lg border border-border p-2 flex gap-2 items-center"
              >
                <span className="text-xs text-muted-foreground w-5 shrink-0">{i + 1}</span>
                {s ? (
                  <>
                    <div className="w-10 h-10 rounded bg-muted relative shrink-0 overflow-hidden">
                      {s.cover_image_url ? (
                        <Image src={s.cover_image_url} alt="" fill className="object-cover" sizes="40px" />
                      ) : (
                        <div className="w-full h-full flex items-center justify-center">
                          <Music className="h-4 w-4 text-muted-foreground" />
                        </div>
                      )}
                    </div>
                    <div className="min-w-0 flex-1">
                      <p className="text-sm font-medium truncate">{s.title}</p>
                      <p className="text-xs text-muted-foreground truncate">{s.artist}</p>
                    </div>
                    <div className="flex flex-col gap-1 shrink-0">
                      <Button type="button" variant="ghost" size="sm" onClick={() => setPickingSlot(i)}>
                        Change
                      </Button>
                      <Button type="button" variant="ghost" size="sm" onClick={() => clearSlot(i)}>
                        Clear
                      </Button>
                    </div>
                  </>
                ) : (
                  <div className="flex-1 flex items-center justify-between gap-2">
                    <span className="text-sm text-muted-foreground">Empty slot</span>
                    <Button type="button" variant="outline" size="sm" onClick={() => setPickingSlot(i)}>
                      Add song
                    </Button>
                  </div>
                )}
              </div>
            ))}

            {pickingSlot !== null && (
              <div className="rounded-lg bg-muted/50 p-3 space-y-2 border border-dashed">
                <p className="text-xs font-medium">Search Spotify for slot {pickingSlot + 1}</p>
                <form onSubmit={runSearch} className="flex gap-2">
                  <Input
                    value={q}
                    onChange={(e) => setQ(e.target.value)}
                    placeholder="Song or artist…"
                    className="flex-1"
                  />
                  <Button type="submit" size="sm" disabled={searching}>
                    {searching ? <Loader2 className="h-4 w-4 animate-spin" /> : <Search className="h-4 w-4" />}
                  </Button>
                </form>
                <Button type="button" variant="ghost" size="sm" onClick={() => setPickingSlot(null)}>
                  Cancel pick
                </Button>
                {results.length > 0 && (
                  <ul className="max-h-40 overflow-y-auto space-y-1 border rounded-md bg-background">
                    {results.map((t) => (
                      <li key={t.spotify_track_id}>
                        <button
                          type="button"
                          className="w-full text-left px-2 py-1.5 text-sm hover:bg-accent rounded-sm"
                          onClick={() => pickTrack(t)}
                        >
                          <span className="font-medium">{t.title}</span>
                          <span className="text-muted-foreground"> — {t.artist}</span>
                        </button>
                      </li>
                    ))}
                  </ul>
                )}
              </div>
            )}

            {error && <p className="text-sm text-destructive">{error}</p>}
          </div>

          <DialogFooter className="p-4 pt-2 border-t shrink-0">
            <Button type="button" variant="outline" onClick={() => setOpen(false)}>
              Cancel
            </Button>
            <Button type="button" onClick={save} disabled={saving}>
              {saving ? <Loader2 className="h-4 w-4 animate-spin" /> : "Save"}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </>
  );
}
