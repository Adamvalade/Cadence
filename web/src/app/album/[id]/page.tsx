"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import Image from "next/image";
import Link from "next/link";
import { Music, Loader2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Separator } from "@/components/ui/separator";
import StarRating from "@/components/StarRating";
import ReviewCard from "@/components/ReviewCard";
import { api } from "@/lib/api";
import { useAuth } from "@/lib/auth";
import type { Album, Review } from "@/lib/types";

export default function AlbumDetailPage() {
  const { id } = useParams<{ id: string }>();
  const { user } = useAuth();
  const [album, setAlbum] = useState<Album | null>(null);
  const [reviews, setReviews] = useState<Review[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!id) return;
    const load = async () => {
      try {
        const [albumData, reviewsData] = await Promise.all([
          api.get<Album>(`/albums/${id}`),
          api.get<Review[]>("/reviews", { username: "", album_id: id }),
        ]);
        setAlbum(albumData);
        setReviews(reviewsData);
      } catch {
        // try just the album
        try {
          const albumData = await api.get<Album>(`/albums/${id}`);
          setAlbum(albumData);
        } catch {
          // album not found
        }
      } finally {
        setLoading(false);
      }
    };
    load();
  }, [id]);

  if (loading) {
    return (
      <div className="flex justify-center py-24">
        <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
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
              <StarRating value={Math.round(album.avg_rating)} size="lg" readonly />
              <p className="text-sm text-muted-foreground">
                {album.review_count} {album.review_count === 1 ? "review" : "reviews"}
              </p>
            </div>
          )}

          {user && (
            <Button render={<Link href={`/album/${id}/review`} />}>Log this album</Button>
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
              <ReviewCard key={review.id} review={review} showAlbum={false} />
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
