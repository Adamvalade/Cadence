"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import Image from "next/image";
import Link from "next/link";
import { Music } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Separator } from "@/components/ui/separator";
import { Skeleton } from "@/components/ui/skeleton";
import StarRating from "@/components/StarRating";
import ReviewCard from "@/components/ReviewCard";
import ListenStatusButton from "@/components/ListenStatusButton";
import AddToListButton from "@/components/AddToListButton";
import { api } from "@/lib/api";
import { useAuth } from "@/lib/auth";
import type { Album, Review } from "@/lib/types";
import { useTitle } from "@/lib/useTitle";

export default function AlbumDetailPage() {
  const { id } = useParams<{ id: string }>();
  const { user } = useAuth();
  const [album, setAlbum] = useState<Album | null>(null);
  const [reviews, setReviews] = useState<Review[]>([]);
  const [listenStatus, setListenStatus] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  useTitle(album ? `${album.title} by ${album.artist}` : undefined);

  useEffect(() => {
    if (!id) return;
    const load = async () => {
      try {
        const albumData = await api.get<Album>(`/albums/${id}`);
        setAlbum(albumData);

        const [reviewsResult, statusResult] = await Promise.allSettled([
          api.get<Review[]>("/reviews", { album_id: id }),
          api.get<{ status: string | null }>(`/listen-status/${id}`),
        ]);
        if (reviewsResult.status === "fulfilled") setReviews(reviewsResult.value);
        if (statusResult.status === "fulfilled") setListenStatus(statusResult.value.status);
      } catch {
        setAlbum(null);
      } finally {
        setLoading(false);
      }
    };
    load();
  }, [id]);

  const handleDeleteReview = (reviewId: string) => {
    setReviews((prev) => prev.filter((r) => r.id !== reviewId));
    if (album) {
      setAlbum({ ...album, review_count: album.review_count - 1 });
    }
  };

  if (loading) {
    return (
      <div className="max-w-4xl mx-auto px-4 py-8">
        <div className="flex flex-col md:flex-row gap-8">
          <Skeleton className="w-64 h-64 rounded-lg shrink-0 mx-auto md:mx-0" />
          <div className="flex-1 space-y-4">
            <Skeleton className="h-9 w-64" />
            <Skeleton className="h-5 w-40" />
            <div className="flex gap-2">
              <Skeleton className="h-6 w-16" />
              <Skeleton className="h-6 w-20" />
            </div>
            <Skeleton className="h-8 w-48" />
          </div>
        </div>
      </div>
    );
  }

  if (!album) {
    return (
      <div className="max-w-2xl mx-auto px-4 py-24 text-center">
        <h1 className="text-2xl font-bold">Album not found</h1>
        <p className="text-muted-foreground mt-2">This album doesn&apos;t exist in our library.</p>
      </div>
    );
  }

  return (
    <div className="max-w-4xl mx-auto px-4 py-8">
      <div className="flex flex-col md:flex-row gap-8">
        <div className="shrink-0">
          <div className="w-64 h-64 rounded-lg overflow-hidden bg-muted relative mx-auto md:mx-0">
            {album.cover_image_url ? (
              <Image
                src={album.cover_image_url}
                alt={album.title}
                fill
                className="object-cover"
                sizes="256px"
                priority
              />
            ) : (
              <div className="w-full h-full flex items-center justify-center">
                <Music className="h-16 w-16 text-muted-foreground/40" />
              </div>
            )}
          </div>
        </div>

        <div className="flex-1 space-y-4">
          <div>
            <h1 className="text-3xl font-bold">{album.title}</h1>
            <p className="text-lg text-muted-foreground">{album.artist}</p>
            <div className="flex items-center gap-2 mt-2">
              {album.release_year && (
                <Badge variant="secondary">{album.release_year}</Badge>
              )}
              {album.genre && (
                <Badge variant="outline">{album.genre}</Badge>
              )}
            </div>
          </div>

          {album.avg_rating != null && (
            <div className="space-y-1">
              <StarRating value={album.avg_rating} size="lg" readonly />
              <p className="text-sm text-muted-foreground">
                {album.review_count} {album.review_count === 1 ? "review" : "reviews"}
              </p>
            </div>
          )}

          {user && (
            <div className="flex items-center gap-2 flex-wrap">
              <Button render={<Link href={`/album/${id}/review`} />}>Log this album</Button>
              <ListenStatusButton
                albumId={id}
                initialStatus={listenStatus as "want_to_listen" | "listening" | "listened" | null}
              />
              <AddToListButton albumId={id} />
            </div>
          )}
        </div>
      </div>

      <Separator className="my-8" />

      <div>
        <h2 className="text-xl font-semibold mb-4">Reviews</h2>
        {reviews.length === 0 ? (
          <p className="text-muted-foreground">No reviews yet. Be the first!</p>
        ) : (
          <div className="space-y-4">
            {reviews.map((review) => (
              <ReviewCard
                key={review.id}
                review={review}
                showAlbum={false}
                onDelete={handleDeleteReview}
              />
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
