"use client";

import { useCallback, useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { Loader2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import ReviewCard from "@/components/ReviewCard";
import { api } from "@/lib/api";
import { useAuth } from "@/lib/auth";
import type { FeedResponse, Review } from "@/lib/types";

export default function FeedPage() {
  const { user, loading: authLoading } = useAuth();
  const router = useRouter();
  const [reviews, setReviews] = useState<Review[]>([]);
  const [loading, setLoading] = useState(true);
  const [hasMore, setHasMore] = useState(false);
  const [cursor, setCursor] = useState<string | null>(null);
  const [loadingMore, setLoadingMore] = useState(false);

  const loadFeed = useCallback(async (nextCursor?: string | null) => {
    const isLoadMore = !!nextCursor;
    if (isLoadMore) setLoadingMore(true);
    else setLoading(true);

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
    } catch {
      // handle error
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

  if (authLoading || loading) {
    return (
      <div className="flex justify-center py-24">
        <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
      </div>
    );
  }

  return (
    <div className="max-w-2xl mx-auto px-4 py-8">
      <h1 className="text-2xl font-bold mb-6">Your Feed</h1>

      {reviews.length === 0 ? (
        <div className="text-center py-12 space-y-3">
          <p className="text-muted-foreground">Your feed is empty.</p>
          <p className="text-sm text-muted-foreground">
            Follow other users to see their reviews here.
          </p>
        </div>
      ) : (
        <div className="space-y-4">
          {reviews.map((review) => (
            <ReviewCard key={review.id} review={review} />
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
