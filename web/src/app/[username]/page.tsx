"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import Link from "next/link";
import Image from "next/image";
import { ExternalLink, Music } from "lucide-react";
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";
import { Button } from "@/components/ui/button";
import { Separator } from "@/components/ui/separator";
import { Skeleton } from "@/components/ui/skeleton";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import ReviewCard from "@/components/ReviewCard";
import FeaturedTracksEditor from "@/components/FeaturedTracksEditor";
import RatingDistribution from "@/components/RatingDistribution";
import UserRatedTracksSection from "@/components/UserRatedTracksSection";
import { api } from "@/lib/api";
import { useAuth } from "@/lib/auth";
import type { Review, UserList, UserProfile } from "@/lib/types";
import { useTitle } from "@/lib/useTitle";
import { formatAverageRatingLabel } from "@/lib/ratingDisplay";

function ProfileSkeleton() {
  return (
    <div className="max-w-3xl mx-auto px-4 py-8">
      <div className="flex items-start gap-6">
        <Skeleton className="h-20 w-20 rounded-full" />
        <div className="flex-1 space-y-3">
          <Skeleton className="h-7 w-48" />
          <Skeleton className="h-4 w-32" />
          <div className="flex gap-4">
            <Skeleton className="h-4 w-20" />
            <Skeleton className="h-4 w-20" />
            <Skeleton className="h-4 w-20" />
          </div>
        </div>
      </div>
    </div>
  );
}

export default function ProfilePage() {
  const { username } = useParams<{ username: string }>();
  const { user: currentUser } = useAuth();

  const [profile, setProfile] = useState<UserProfile | null>(null);
  const [reviews, setReviews] = useState<Review[]>([]);
  const [lists, setLists] = useState<UserList[]>([]);
  const [loading, setLoading] = useState(true);
  const [isFollowing, setIsFollowing] = useState(false);

  useTitle(profile ? `${profile.display_name || profile.username} (@${profile.username})` : undefined);

  useEffect(() => {
    if (!username) return;
    const load = async () => {
      try {
        const profileData = await api.get<UserProfile>(`/users/${username}`);
        setProfile(profileData);

        const [reviewsData, listsData] = await Promise.allSettled([
          api.get<Review[]>("/reviews", { username }),
          api.get<UserList[]>("/lists", { username }),
        ]);
        if (reviewsData.status === "fulfilled") setReviews(reviewsData.value);
        if (listsData.status === "fulfilled") setLists(listsData.value);

        if (currentUser && currentUser.username !== username) {
          try {
            const status = await api.get<{ following: boolean }>(`/users/${profileData.id}/follow/status`);
            setIsFollowing(status.following);
          } catch {
            /* not authenticated */
          }
        }
      } catch {
        setProfile(null);
      } finally {
        setLoading(false);
      }
    };
    load();
  }, [username, currentUser]);

  const handleFollow = async () => {
    if (!profile) return;
    try {
      if (isFollowing) {
        await api.delete(`/users/${profile.id}/follow`);
        setIsFollowing(false);
        setProfile((p) => p ? { ...p, follower_count: p.follower_count - 1 } : p);
      } else {
        await api.post(`/users/${profile.id}/follow`);
        setIsFollowing(true);
        setProfile((p) => p ? { ...p, follower_count: p.follower_count + 1 } : p);
      }
    } catch {
      // handle error
    }
  };

  const handleDeleteReview = async (reviewId: string) => {
    setReviews((prev) => prev.filter((r) => r.id !== reviewId));
    if (!username) return;
    try {
      const p = await api.get<UserProfile>(`/users/${username}`);
      setProfile(p);
    } catch {
      /* keep stale stats */
    }
  };

  if (loading) {
    return <ProfileSkeleton />;
  }

  if (!profile) {
    return (
      <div className="max-w-2xl mx-auto px-4 py-24 text-center">
        <h1 className="text-2xl font-bold">User not found</h1>
        <p className="text-muted-foreground mt-2">This user doesn&apos;t exist or couldn&apos;t be loaded.</p>
      </div>
    );
  }

  const isOwnProfile = currentUser?.username === profile.username;

  return (
    <div className="max-w-3xl mx-auto px-3 py-5 sm:px-4 sm:py-6">
      <div className="flex items-start gap-4 sm:gap-5">
        <Avatar className="h-20 w-20">
          <AvatarImage src={profile.avatar_url || undefined} alt={profile.username} />
          <AvatarFallback className="text-2xl">{profile.username[0].toUpperCase()}</AvatarFallback>
        </Avatar>

        <div className="flex-1 space-y-2">
          <div className="flex items-center gap-3">
            <h1 className="text-2xl font-bold">{profile.display_name || profile.username}</h1>
            <span className="text-muted-foreground">@{profile.username}</span>
          </div>

          {profile.bio && <p className="text-sm text-muted-foreground">{profile.bio}</p>}

          <div className="flex items-center gap-4 text-sm">
            <span><strong>{profile.review_count}</strong> reviews</span>
            <span><strong>{profile.follower_count}</strong> followers</span>
            <span><strong>{profile.following_count}</strong> following</span>
          </div>

          {currentUser && !isOwnProfile && (
            <Button
              variant={isFollowing ? "outline" : "default"}
              size="sm"
              onClick={handleFollow}
            >
              {isFollowing ? "Unfollow" : "Follow"}
            </Button>
          )}
          <div className="flex flex-wrap gap-2">
            {isOwnProfile && (
              <>
                <Button variant="outline" size="sm" render={<Link href="/settings" />}>
                  Edit profile
                </Button>
                <FeaturedTracksEditor profile={profile} onSaved={setProfile} />
              </>
            )}
          </div>
        </div>
      </div>

      <div className="mt-5 grid grid-cols-2 gap-2 md:grid-cols-4 md:gap-3">
        <div className="rounded-lg border border-border bg-card p-3">
          <p className="text-xs text-muted-foreground uppercase tracking-wide">Album ratings</p>
          <p className="text-2xl font-semibold tabular-nums mt-1">{profile.rating_stats.album_ratings_count}</p>
          <p className="text-sm text-muted-foreground mt-0.5">
            Avg{" "}
            {profile.rating_stats.album_ratings_average != null
              ? formatAverageRatingLabel(profile.rating_stats.album_ratings_average)
              : "—"}
          </p>
        </div>
        <div className="rounded-lg border border-border bg-card p-3">
          <p className="text-xs text-muted-foreground uppercase tracking-wide">Song ratings</p>
          <p className="text-2xl font-semibold tabular-nums mt-1">{profile.rating_stats.song_ratings_count}</p>
          <p className="text-sm text-muted-foreground mt-0.5">
            Avg{" "}
            {profile.rating_stats.song_ratings_average != null
              ? formatAverageRatingLabel(profile.rating_stats.song_ratings_average)
              : "—"}
          </p>
        </div>
        <div className="rounded-lg border border-border bg-card p-3 col-span-2 md:col-span-2">
          <p className="text-xs text-muted-foreground uppercase tracking-wide">All ratings</p>
          <p className="text-2xl font-semibold tabular-nums mt-1">
            {profile.rating_stats.album_ratings_count + profile.rating_stats.song_ratings_count}
          </p>
          <p className="text-sm text-muted-foreground mt-0.5">Album + per-track scores you&apos;ve given</p>
        </div>
      </div>

      {profile.rating_stats.album_ratings_count + profile.rating_stats.song_ratings_count > 0 && (
        <div className="mt-5 rounded-lg border border-border bg-card p-3 sm:p-4">
          <RatingDistribution distribution={profile.rating_stats.combined_rating_distribution} />
        </div>
      )}

      <div className="mt-6">
        <h2 className="text-base font-semibold mb-2">Featured songs</h2>
        {profile.featured_tracks.length === 0 ? (
          <p className="text-sm text-muted-foreground">
            {isOwnProfile
              ? "Show up to 5 songs you’re replaying—use Edit featured songs above."
              : "No featured songs yet."}
          </p>
        ) : (
          <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-5 gap-3">
            {profile.featured_tracks.map((f) => (
              <a
                key={`${f.slot}-${f.spotify_track_id}`}
                href={f.open_url}
                target="_blank"
                rel="noopener noreferrer"
                className="group rounded-lg border border-border bg-card overflow-hidden hover:bg-accent/40 transition-colors"
              >
                <div className="aspect-square bg-muted relative">
                  {f.cover_image_url ? (
                    <Image src={f.cover_image_url} alt="" fill className="object-cover" sizes="(max-width:768px) 50vw, 20vw" />
                  ) : (
                    <div className="w-full h-full flex items-center justify-center">
                      <Music className="h-10 w-10 text-muted-foreground/50" />
                    </div>
                  )}
                </div>
                <div className="p-2">
                  <p className="text-xs font-medium line-clamp-2">{f.title}</p>
                  <p className="text-[11px] text-muted-foreground line-clamp-1">{f.artist}</p>
                  <span className="inline-flex items-center gap-0.5 text-[10px] text-muted-foreground mt-1">
                    Spotify <ExternalLink className="h-2.5 w-2.5" />
                  </span>
                </div>
              </a>
            ))}
          </div>
        )}
      </div>

      <Separator className="my-6" />

      <Tabs defaultValue="reviews">
        <TabsList>
          <TabsTrigger value="reviews">Reviews ({reviews.length})</TabsTrigger>
          <TabsTrigger value="lists">Lists ({lists.length})</TabsTrigger>
        </TabsList>

        <TabsContent value="reviews" className="mt-3 space-y-3">
          {reviews.length === 0 ? (
            <div className="text-center py-8 space-y-2">
              <p className="text-muted-foreground">No reviews yet.</p>
              {isOwnProfile && (
                <Button variant="outline" size="sm" render={<Link href="/search" />}>
                  Search for an album to review
                </Button>
              )}
            </div>
          ) : (
            reviews.map((review) => (
              <ReviewCard key={review.id} review={review} onDelete={handleDeleteReview} />
            ))
          )}
        </TabsContent>

        <TabsContent value="lists" className="mt-3 space-y-2">
          {lists.length === 0 ? (
            <div className="text-center py-8 space-y-2">
              <p className="text-muted-foreground">No lists yet.</p>
              {isOwnProfile && (
                <p className="text-sm text-muted-foreground">
                  Visit an album page and use &ldquo;Add to list&rdquo; to create your first list.
                </p>
              )}
            </div>
          ) : (
            lists.map((list) => (
              <Link key={list.id} href={`/lists/${list.id}`} className="block">
                <div className="border rounded-lg p-3 hover:bg-accent/50 transition-colors">
                  <h3 className="font-medium">{list.title}</h3>
                  {list.description && (
                    <p className="text-sm text-muted-foreground mt-1">{list.description}</p>
                  )}
                </div>
              </Link>
            ))
          )}
        </TabsContent>
      </Tabs>

      {profile.rating_stats.song_ratings_count > 0 && (
        <UserRatedTracksSection username={profile.username} isOwnProfile={isOwnProfile} />
      )}
    </div>
  );
}
