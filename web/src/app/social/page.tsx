"use client";

import { useCallback, useEffect, useState } from "react";
import Link from "next/link";
import { Loader2, Users } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";
import ReviewCard from "@/components/ReviewCard";
import { api } from "@/lib/api";
import { useAuth } from "@/lib/auth";
import { useTitle } from "@/lib/useTitle";
import type { DiscoverUser, FeedResponse, Review } from "@/lib/types";

export default function SocialPage() {
  useTitle("Social");
  const { user, loading: authLoading } = useAuth();

  const [recent, setRecent] = useState<Review[]>([]);
  const [popular, setPopular] = useState<Review[]>([]);
  const [people, setPeople] = useState<DiscoverUser[]>([]);
  const [followingFeed, setFollowingFeed] = useState<Review[]>([]);
  const [feedHasMore, setFeedHasMore] = useState(false);
  const [feedCursor, setFeedCursor] = useState<string | null>(null);
  const [followingInitialLoading, setFollowingInitialLoading] = useState(false);
  const [loadingMoreFeed, setLoadingMoreFeed] = useState(false);

  const [loadingLists, setLoadingLists] = useState(true);
  const [tab, setTab] = useState("community");

  useEffect(() => {
    const load = async () => {
      const [r, p, u] = await Promise.allSettled([
        api.get<Review[]>("/discover/recent-reviews", { limit: "25" }),
        api.get<Review[]>("/discover/popular-reviews", { limit: "15" }),
        api.get<DiscoverUser[]>("/discover/active-users", { limit: "20" }),
      ]);
      if (r.status === "fulfilled") setRecent(r.value);
      if (p.status === "fulfilled") setPopular(p.value);
      if (u.status === "fulfilled") setPeople(u.value);
      setLoadingLists(false);
    };
    void load();
  }, []);

  const loadFollowingPage = useCallback(async (cursor?: string | null) => {
    if (!user) return;
    const isMore = !!cursor;
    if (isMore) setLoadingMoreFeed(true);
    else setFollowingInitialLoading(true);
    try {
      const params: Record<string, string> = { limit: "15" };
      if (cursor) params.cursor = cursor;
      const data = await api.get<FeedResponse>("/feed", params);
      if (isMore) {
        setFollowingFeed((prev) => [...prev, ...data.items]);
      } else {
        setFollowingFeed(data.items);
      }
      setFeedHasMore(data.has_more);
      setFeedCursor(data.next_cursor);
    } finally {
      if (isMore) setLoadingMoreFeed(false);
      else setFollowingInitialLoading(false);
    }
  }, [user]);

  useEffect(() => {
    if (authLoading || !user || tab !== "following") return;
    void loadFollowingPage();
  }, [authLoading, user, tab, loadFollowingPage]);

  return (
    <div className="max-w-3xl mx-auto px-4 py-8">
      <div className="flex items-center gap-2 mb-2">
        <Users className="h-7 w-7" />
        <h1 className="text-2xl font-bold">Social</h1>
      </div>
      <p className="text-sm text-muted-foreground mb-6">
        Community reviews, popular posts, and people to follow. Your personalized feed from people you follow
        is also here when you&apos;re signed in.
      </p>

      <Tabs value={tab} onValueChange={setTab}>
        <TabsList className="flex flex-wrap h-auto gap-1">
          <TabsTrigger value="community">Community</TabsTrigger>
          <TabsTrigger value="popular">Popular</TabsTrigger>
          <TabsTrigger value="people">People</TabsTrigger>
          <TabsTrigger value="following">Following</TabsTrigger>
        </TabsList>

        <TabsContent value="community" className="mt-6">
          {loadingLists ? (
            <div className="flex justify-center py-12">
              <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
            </div>
          ) : recent.length === 0 ? (
            <p className="text-muted-foreground text-center py-8">No reviews yet.</p>
          ) : (
            <div className="space-y-4">
              {recent.map((review) => (
                <ReviewCard key={review.id} review={review} />
              ))}
            </div>
          )}
        </TabsContent>

        <TabsContent value="popular" className="mt-6">
          {loadingLists ? (
            <div className="flex justify-center py-12">
              <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
            </div>
          ) : popular.length === 0 ? (
            <p className="text-muted-foreground text-center py-8">No popular reviews yet.</p>
          ) : (
            <div className="space-y-4">
              {popular.map((review) => (
                <ReviewCard key={review.id} review={review} />
              ))}
            </div>
          )}
        </TabsContent>

        <TabsContent value="people" className="mt-6">
          {loadingLists ? (
            <div className="flex justify-center py-12">
              <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
            </div>
          ) : people.length === 0 ? (
            <p className="text-muted-foreground text-center py-8">
              No one to show yet. Try <Link href="/search" className="underline">Search</Link> to find users by
              name.
            </p>
          ) : (
            <ul className="space-y-2">
              {people.map((u) => (
                <li key={u.id}>
                  <Link
                    href={`/${u.username}`}
                    className="flex items-center gap-3 rounded-lg border p-3 hover:bg-accent/50 transition-colors"
                  >
                    <Avatar className="h-10 w-10">
                      <AvatarImage src={u.avatar_url || undefined} alt="" />
                      <AvatarFallback>{u.username[0].toUpperCase()}</AvatarFallback>
                    </Avatar>
                    <div className="flex-1 min-w-0">
                      <p className="font-medium text-sm truncate">{u.display_name}</p>
                      <p className="text-xs text-muted-foreground truncate">@{u.username}</p>
                    </div>
                    <span className="text-xs text-muted-foreground shrink-0">
                      {u.review_count} {u.review_count === 1 ? "review" : "reviews"}
                    </span>
                  </Link>
                </li>
              ))}
            </ul>
          )}
        </TabsContent>

        <TabsContent value="following" className="mt-6">
          {!user ? (
            <div className="text-center py-12 space-y-3">
              <p className="text-muted-foreground">Sign in to see reviews from people you follow.</p>
              <Button render={<Link href="/auth/login" />}>Log in</Button>
            </div>
          ) : followingInitialLoading ? (
            <div className="flex justify-center py-12">
              <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
            </div>
          ) : followingFeed.length === 0 ? (
            <div className="text-center py-12 space-y-4">
              <p className="text-muted-foreground">
                You&apos;re not following anyone yet, or they haven&apos;t posted reviews.
              </p>
              <div className="flex gap-2 justify-center flex-wrap">
                <Button variant="outline" onClick={() => setTab("people")}>
                  Browse people
                </Button>
                <Button variant="outline" render={<Link href="/search" />}>
                  Search users
                </Button>
              </div>
            </div>
          ) : (
            <div className="space-y-4">
              {followingFeed.map((review) => (
                <ReviewCard key={review.id} review={review} />
              ))}
              {feedHasMore && (
                <div className="flex justify-center pt-2">
                  <Button
                    variant="outline"
                    disabled={loadingMoreFeed}
                    onClick={() => void loadFollowingPage(feedCursor)}
                  >
                    {loadingMoreFeed ? (
                      <Loader2 className="h-4 w-4 animate-spin mr-2" />
                    ) : null}
                    Load more
                  </Button>
                </div>
              )}
            </div>
          )}
        </TabsContent>
      </Tabs>
    </div>
  );
}
