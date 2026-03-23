"use client";

import { useCallback, useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { Loader2, Music } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import ReviewCard from "@/components/ReviewCard";
import { api } from "@/lib/api";
import { useAuth } from "@/lib/auth";
import { useTitle } from "@/lib/useTitle";
import type { FeedResponse, Review } from "@/lib/types";

function FeedSkeleton() {
  return (
    <div className="space-y-4">
      {[1, 2, 3].map((i) => (
        <div key={i} className="border rounded-lg p-4 flex gap-4">
          <Skeleton className="w-20 h-20 rounded-md shrink-0" />
          <div className="flex-1 space-y-2">
            <Skeleton className="h-4 w-32" />
            <Skeleton className="h-3 w-48" />
            <Skeleton className="h-4 w-24" />
            <Skeleton className="h-3 w-full" />
          </div>
        </div>
      ))}
    </div>
  );
}

export default function FeedPage() {
  useTitle("Feed");
  const { user, loading: authLoading } = useAuth();
  const router = useRouter();
  const [reviews, setReviews] = useState<Review[]>([]);
  const [loading, setLoading] = useState(true);
  const [hasMore, setHasMore] = useState(false);
  const [cursor, setCursor] = useState<string | null>(null);
  const [loadingMore, setLoadingMore] = useState(false);
  const [error, setError] = useState("");

  const loadFeed = useCallback(async (nextCursor?: string | null) => {
    const isLoadMore = !!nextCursor;
    if (isLoadMore) setLoadingMore(true);
    else setLoading(true);
    setError("");

    try {
      const params: Record<string, string> = {};
      if (nextCursor) params.cursor = nextCursor;

      const data = await api.get<FeedResponse>("/feed", params);
      if (isLoadMore) {
        setReviews((prev) => [...prev, ...data.items]);
      } else {
        setReviews(data.items);
      }
      setHasMore(data.has_more);
      setCursor(data.next_cursor);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load feed");
    } finally {
      setLoading(false);
      setLoadingMore(false);
    }
  }, []);

  useEffect(() => {
    if (authLoading) return;
    if (!user) {
      router.push("/auth/login");
      return;
    }
    loadFeed();
  }, [user, authLoading, router, loadFeed]);

  const handleDeleteReview = (reviewId: string) => {
    setReviews((prev) => prev.filter((r) => r.id !== reviewId));
  };

  if (authLoading || loading) {
    return (
      <div className="max-w-2xl mx-auto px-4 py-8">
        <h1 className="text-2xl font-bold mb-6">Your Feed</h1>
        <FeedSkeleton />
      </div>
    );
  }

  return (
    <div className="max-w-2xl mx-auto px-4 py-8">
      <h1 className="text-2xl font-bold mb-6">Your Feed</h1>

      {error ? (
        <div className="text-center py-12 space-y-3">
          <p className="text-destructive font-medium">Something went wrong</p>
          <p className="text-sm text-muted-foreground">{error}</p>
          <Button variant="outline" onClick={() => loadFeed()}>Try again</Button>
        </div>
      ) : reviews.length === 0 ? (
        <div className="text-center py-16 space-y-4">
          <div className="mx-auto w-16 h-16 rounded-full bg-muted flex items-center justify-center">
            <Music className="h-8 w-8 text-muted-foreground/50" />
          </div>
          <div className="space-y-1">
            <p className="font-medium text-lg">Your feed is empty</p>
            <p className="text-sm text-muted-foreground max-w-sm mx-auto">
              Follow other users to see their reviews here, or discover trending albums.
            </p>
          </div>
          <div className="flex gap-2 justify-center">
            <Button variant="outline" render={<Link href="/discover" />}>Discover</Button>
            <Button render={<Link href="/search" />}>Search albums</Button>
          </div>
        </div>
      ) : (
        <div className="space-y-4">
          {reviews.map((review) => (
            <ReviewCard key={review.id} review={review} onDelete={handleDeleteReview} />
          ))}

          {hasMore && (
            <div className="flex justify-center pt-4">
              <Button variant="outline" onClick={() => loadFeed(cursor)} disabled={loadingMore}>
                {loadingMore ? (
                  <Loader2 className="h-4 w-4 animate-spin mr-2" />
                ) : null}
                Load more
              </Button>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
