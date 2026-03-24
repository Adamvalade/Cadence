"use client";

import { useEffect, useState } from "react";
import Image from "next/image";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { Search, Music, Loader2 } from "lucide-react";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { useTitle } from "@/lib/useTitle";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";
import { api } from "@/lib/api";
import {
  clearRecentSearches,
  pushRecentSearch,
  readRecentSearches,
} from "@/lib/recentSearches";
import type { Album, AlbumSearchResult } from "@/lib/types";

interface UserSearchResult {
  id: string;
  username: string;
  display_name: string;
  avatar_url: string | null;
  review_count: number;
}

export default function SearchPage() {
  useTitle("Search");
  const [query, setQuery] = useState("");
  const [albumResults, setAlbumResults] = useState<AlbumSearchResult[]>([]);
  const [userResults, setUserResults] = useState<UserSearchResult[]>([]);
  const [loading, setLoading] = useState(false);
  const [searched, setSearched] = useState(false);
  const [tab, setTab] = useState("albums");
  const [importingSpotifyId, setImportingSpotifyId] = useState<string | null>(null);
  const [importError, setImportError] = useState<string | null>(null);
  const [recent, setRecent] = useState<string[]>([]);
  const router = useRouter();

  useEffect(() => {
    setRecent(readRecentSearches());
  }, []);

  const executeSearch = async (raw: string) => {
    const trimmed = raw.trim();
    if (!trimmed) return;
    setLoading(true);
    setSearched(true);
    setQuery(trimmed);

    const [albums, users] = await Promise.allSettled([
      api.get<AlbumSearchResult[]>("/albums/search", { q: trimmed }),
      api.get<UserSearchResult[]>("/discover/users", { q: trimmed }),
    ]);
    setAlbumResults(albums.status === "fulfilled" ? albums.value : []);
    setUserResults(users.status === "fulfilled" ? users.value : []);
    setLoading(false);

    pushRecentSearch(trimmed);
    setRecent(readRecentSearches());
  };

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    void executeSearch(query);
  };

  const handleImport = async (spotifyId: string) => {
    setImportError(null);
    setImportingSpotifyId(spotifyId);
    try {
      const album = await api.post<Album>(`/albums/import/${spotifyId}`);
      router.push(`/album/${album.id}`);
    } catch (e) {
      setImportError(e instanceof Error ? e.message : "Could not open this album.");
    } finally {
      setImportingSpotifyId(null);
    }
  };

  const handleClick = (result: AlbumSearchResult) => {
    if (importingSpotifyId) return;
    if (result.existing_id) {
      router.push(`/album/${result.existing_id}`);
    } else {
      void handleImport(result.spotify_id);
    }
  };

  return (
    <div className="max-w-2xl mx-auto px-4 py-8">
      <h1 className="text-2xl font-bold mb-6">Search</h1>

      <form onSubmit={handleSearch} className="flex gap-2 mb-6">
        <div className="relative flex-1">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
          <Input
            placeholder="Search for albums, artists, or users..."
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            className="pl-9"
          />
        </div>
        <Button type="submit" disabled={loading}>
          {loading ? <Loader2 className="h-4 w-4 animate-spin" /> : "Search"}
        </Button>
      </form>

      {recent.length > 0 && (
        <div className="mb-6">
          <div className="flex items-center justify-between gap-2 mb-2">
            <p className="text-xs font-medium text-muted-foreground">Recent searches</p>
            <button
              type="button"
              className="text-xs text-muted-foreground hover:text-foreground"
              onClick={() => {
                clearRecentSearches();
                setRecent([]);
              }}
            >
              Clear
            </button>
          </div>
          <div className="flex flex-wrap gap-2">
            {recent.map((term) => (
              <Button
                key={term}
                type="button"
                variant="outline"
                size="sm"
                className="h-8 text-xs font-normal"
                disabled={loading}
                onClick={() => void executeSearch(term)}
              >
                {term}
              </Button>
            ))}
          </div>
        </div>
      )}

      {loading && (
        <div className="flex justify-center py-12">
          <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
        </div>
      )}

      {!loading && searched && (
        <Tabs value={tab} onValueChange={setTab}>
          <TabsList>
            <TabsTrigger value="albums">Albums ({albumResults.length})</TabsTrigger>
            <TabsTrigger value="users">Users ({userResults.length})</TabsTrigger>
          </TabsList>

          {importError && (
            <p className="mt-4 text-sm text-destructive" role="alert">
              {importError}
            </p>
          )}

          <TabsContent value="albums" className="mt-4 space-y-2">
            {albumResults.length === 0 ? (
              <p className="text-center text-muted-foreground py-8">
                No albums found. Try a different search term.
              </p>
            ) : (
              albumResults.map((result) => (
                <Card
                  key={result.spotify_id}
                  className={`cursor-pointer hover:bg-accent/50 transition-colors ${importingSpotifyId === result.spotify_id ? "opacity-70 pointer-events-none" : ""}`}
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
                    {importingSpotifyId === result.spotify_id ? (
                      <Loader2 className="h-4 w-4 animate-spin text-muted-foreground shrink-0" />
                    ) : result.existing_id ? (
                      <span className="text-xs text-muted-foreground bg-muted px-2 py-1 rounded">
                        In library
                      </span>
                    ) : null}
                  </CardContent>
                </Card>
              ))
            )}
          </TabsContent>

          <TabsContent value="users" className="mt-4 space-y-2">
            {userResults.length === 0 ? (
              <p className="text-center text-muted-foreground py-8">
                No users found.
              </p>
            ) : (
              userResults.map((user) => (
                <Link key={user.id} href={`/${user.username}`}>
                  <Card className="hover:bg-accent/50 transition-colors">
                    <CardContent className="p-3 flex items-center gap-4">
                      <Avatar className="h-10 w-10">
                        <AvatarImage src={user.avatar_url || undefined} />
                        <AvatarFallback>{user.username[0].toUpperCase()}</AvatarFallback>
                      </Avatar>
                      <div className="flex-1 min-w-0">
                        <p className="font-medium text-sm">{user.display_name}</p>
                        <p className="text-xs text-muted-foreground">@{user.username}</p>
                      </div>
                      <span className="text-xs text-muted-foreground">
                        {user.review_count} {user.review_count === 1 ? "review" : "reviews"}
                      </span>
                    </CardContent>
                  </Card>
                </Link>
              ))
            )}
          </TabsContent>
        </Tabs>
      )}
    </div>
  );
}
