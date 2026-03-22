"use client";

import { useState } from "react";
import Image from "next/image";
import { useRouter } from "next/navigation";
import { Search, Music, Loader2 } from "lucide-react";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { api } from "@/lib/api";
import type { AlbumSearchResult } from "@/lib/types";

export default function SearchPage() {
  const [query, setQuery] = useState("");
  const [results, setResults] = useState<AlbumSearchResult[]>([]);
  const [loading, setLoading] = useState(false);
  const [searched, setSearched] = useState(false);
  const router = useRouter();

  const handleSearch = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!query.trim()) return;
    setLoading(true);
    setSearched(true);
    try {
      const data = await api.get<AlbumSearchResult[]>("/albums/search", { q: query });
      setResults(data);
    } catch {
      setResults([]);
    } finally {
      setLoading(false);
    }
  };

  const handleImport = async (spotifyId: string) => {
    try {
      const album = await api.post<{ id: string }>(`/albums/import/${spotifyId}`);
      router.push(`/album/${album.id}`);
    } catch {
      // handle error
    }
  };

  const handleClick = (result: AlbumSearchResult) => {
    if (result.existing_id) {
      router.push(`/album/${result.existing_id}`);
    } else {
      handleImport(result.spotify_id);
    }
  };

  return (
    <div className="max-w-2xl mx-auto px-4 py-8">
      <h1 className="text-2xl font-bold mb-6">Search Albums</h1>

      <form onSubmit={handleSearch} className="flex gap-2 mb-8">
        <div className="relative flex-1">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
          <Input
            placeholder="Search for an album or artist..."
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            className="pl-9"
          />
        </div>
        <Button type="submit" disabled={loading}>
          {loading ? <Loader2 className="h-4 w-4 animate-spin" /> : "Search"}
        </Button>
      </form>

      {loading && (
        <div className="flex justify-center py-12">
          <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
        </div>
      )}

      {!loading && searched && results.length === 0 && (
        <p className="text-center text-muted-foreground py-12">
          No albums found. Try a different search term.
        </p>
      )}

      <div className="space-y-2">
        {results.map((result) => (
          <Card
            key={result.spotify_id}
            className="cursor-pointer hover:bg-accent/50 transition-colors"
            onClick={() => handleClick(result)}
          >
            <CardContent className="p-3 flex items-center gap-4">
              <div className="w-14 h-14 rounded-md overflow-hidden bg-muted relative shrink-0">
                {result.cover_image_url ? (
                  <Image
                    src={result.cover_image_url}
                    alt={result.title}
                    fill
                    className="object-cover"
                    sizes="56px"
                  />
                ) : (
                  <div className="w-full h-full flex items-center justify-center">
                    <Music className="h-5 w-5 text-muted-foreground/40" />
                  </div>
                )}
              </div>
              <div className="flex-1 min-w-0">
                <p className="font-medium text-sm truncate">{result.title}</p>
                <p className="text-xs text-muted-foreground truncate">{result.artist}</p>
                {result.release_year && (
                  <p className="text-xs text-muted-foreground">{result.release_year}</p>
                )}
              </div>
              {result.existing_id && (
                <span className="text-xs text-muted-foreground bg-muted px-2 py-1 rounded">
                  In library
                </span>
              )}
            </CardContent>
          </Card>
        ))}
      </div>
    </div>
  );
}
