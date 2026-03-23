"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import Image from "next/image";
import { Loader2, Music, TrendingUp } from "lucide-react";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Skeleton } from "@/components/ui/skeleton";
import ReviewCard from "@/components/ReviewCard";
import { api } from "@/lib/api";
import { useTitle } from "@/lib/useTitle";
import type { Album, Review } from "@/lib/types";

function AlbumGrid({ albums }: { albums: Album[] }) {
  if (albums.length === 0) {
    return <p className="text-muted-foreground text-center py-8">No trending albums yet.</p>;
  }
  return (
    <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 gap-4">
      {albums.map((album) => (
        <Link key={album.id} href={`/album/${album.id}`} className="group space-y-2">
          <div className="aspect-square rounded-lg overflow-hidden bg-muted relative">
            {album.cover_image_url ? (
              <Image
                src={album.cover_image_url}
                alt={album.title}
                fill
                className="object-cover group-hover:scale-105 transition-transform"
                sizes="(max-width: 640px) 50vw, (max-width: 768px) 33vw, 20vw"
              />
            ) : (
              <div className="w-full h-full flex items-center justify-center">
                <Music className="h-8 w-8 text-muted-foreground/40" />
              </div>
            )}
          </div>
          <div className="space-y-0.5">
            <p className="text-sm font-medium truncate">{album.title}</p>
            <p className="text-xs text-muted-foreground truncate">{album.artist}</p>
            <div className="flex items-center gap-1 text-xs text-muted-foreground">
              {album.avg_rating != null && <span>{album.avg_rating}/10</span>}
              {album.avg_rating != null && <span>&middot;</span>}
              <span>{album.review_count} {album.review_count === 1 ? "review" : "reviews"}</span>
            </div>
          </div>
        </Link>
      ))}
    </div>
  );
}

function AlbumGridSkeleton() {
  return (
    <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 gap-4">
      {[1, 2, 3, 4, 5, 6, 7, 8, 9, 10].map((i) => (
        <div key={i} className="space-y-2">
          <Skeleton className="aspect-square rounded-lg" />
          <Skeleton className="h-4 w-3/4" />
          <Skeleton className="h-3 w-1/2" />
        </div>
      ))}
    </div>
  );
}

export default function DiscoverPage() {
  useTitle("Discover");
  const [trending, setTrending] = useState<Album[]>([]);
  const [recentReviews, setRecentReviews] = useState<Review[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const load = async () => {
      const [trendingResult, recentResult] = await Promise.allSettled([
        api.get<Album[]>("/discover/trending-albums"),
        api.get<Review[]>("/discover/recent-reviews"),
      ]);
      if (trendingResult.status === "fulfilled") setTrending(trendingResult.value);
      if (recentResult.status === "fulfilled") setRecentReviews(recentResult.value);
      setLoading(false);
    };
    load();
  }, []);

  return (
    <div className="max-w-5xl mx-auto px-4 py-8">
      <div className="flex items-center gap-2 mb-6">
        <TrendingUp className="h-6 w-6" />
        <h1 className="text-2xl font-bold">Discover</h1>
      </div>

      <Tabs defaultValue="trending">
        <TabsList>
          <TabsTrigger value="trending">Trending Albums</TabsTrigger>
          <TabsTrigger value="recent">Recent Reviews</TabsTrigger>
        </TabsList>

        <TabsContent value="trending" className="mt-6">
          {loading ? <AlbumGridSkeleton /> : <AlbumGrid albums={trending} />}
        </TabsContent>

        <TabsContent value="recent" className="mt-6">
          {loading ? (
            <div className="flex justify-center py-12">
              <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
            </div>
          ) : recentReviews.length === 0 ? (
            <p className="text-muted-foreground text-center py-8">No reviews yet. Be the first!</p>
          ) : (
            <div className="space-y-4 max-w-2xl">
              {recentReviews.map((review) => (
                <ReviewCard key={review.id} review={review} />
              ))}
            </div>
          )}
        </TabsContent>
      </Tabs>
    </div>
  );
}
