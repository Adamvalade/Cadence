"use client";

import { useEffect, useState } from "react";
import { useParams, useRouter, useSearchParams } from "next/navigation";
import Image from "next/image";
import { Music } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Checkbox } from "@/components/ui/checkbox";
import { useTitle } from "@/lib/useTitle";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import StarRating from "@/components/StarRating";
import { api } from "@/lib/api";
import { useAuth } from "@/lib/auth";
import type { Album, Review } from "@/lib/types";

export default function ReviewPage() {
  useTitle("Write a Review");
  const { id } = useParams<{ id: string }>();
  const searchParams = useSearchParams();
  const editId = searchParams.get("edit");
  const { user, loading: authLoading } = useAuth();
  const router = useRouter();

  const [album, setAlbum] = useState<Album | null>(null);
  const [rating, setRating] = useState(0);
  const [body, setBody] = useState("");
  const [isRelisten, setIsRelisten] = useState(false);
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    if (!id) return;
    const load = async () => {
      try {
        const albumData = await api.get<Album>(`/albums/${id}`);
        setAlbum(albumData);

        if (editId) {
          const review = await api.get<Review>(`/reviews/${editId}`);
          setRating(review.rating);
          setBody(review.body || "");
          setIsRelisten(review.is_relisten);
        }
      } catch {
        // album or review not found
      } finally {
        setLoading(false);
      }
    };
    load();
  }, [id, editId]);

  useEffect(() => {
    if (!user && !authLoading) {
      router.push("/auth/login");
    }
  }, [user, authLoading, router]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (rating === 0) {
      setError("Please select a rating");
      return;
    }
    setError("");
    setSubmitting(true);
    try {
      if (editId) {
        await api.patch(`/reviews/${editId}`, {
          rating,
          body: body || null,
          is_relisten: isRelisten,
        });
      } else {
        await api.post("/reviews", {
          album_id: id,
          rating,
          body: body || null,
          is_relisten: isRelisten,
        });
      }
      router.push(`/album/${id}`);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to submit review");
    } finally {
      setSubmitting(false);
    }
  };

  if (loading) {
    return (
      <div className="max-w-xl mx-auto px-4 py-8">
        <Card>
          <CardHeader>
            <div className="flex items-center gap-4 mb-2">
              <Skeleton className="w-16 h-16 rounded-md" />
              <div className="space-y-2">
                <Skeleton className="h-5 w-32" />
                <Skeleton className="h-3 w-24" />
              </div>
            </div>
          </CardHeader>
          <CardContent className="space-y-6">
            <Skeleton className="h-6 w-48" />
            <Skeleton className="h-24 w-full" />
            <Skeleton className="h-10 w-full" />
          </CardContent>
        </Card>
      </div>
    );
  }

  if (!album) {
    return (
      <div className="max-w-2xl mx-auto px-4 py-24 text-center">
        <h1 className="text-2xl font-bold">Album not found</h1>
      </div>
    );
  }

  return (
    <div className="max-w-xl mx-auto px-4 py-8">
      <Card>
        <CardHeader>
          <div className="flex items-center gap-4 mb-2">
            <div className="w-16 h-16 rounded-md overflow-hidden bg-muted relative shrink-0">
              {album.cover_image_url ? (
                <Image
                  src={album.cover_image_url}
                  alt={album.title}
                  fill
                  className="object-cover"
                  sizes="64px"
                />
              ) : (
                <div className="w-full h-full flex items-center justify-center">
                  <Music className="h-6 w-6 text-muted-foreground/40" />
                </div>
              )}
            </div>
            <div>
              <CardTitle className="text-lg">{album.title}</CardTitle>
              <p className="text-sm text-muted-foreground">{album.artist}</p>
            </div>
          </div>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleSubmit} className="space-y-6">
            {error && (
              <div className="bg-destructive/10 text-destructive text-sm p-3 rounded-md">
                {error}
              </div>
            )}

            <div className="space-y-2">
              <Label>Rating</Label>
              <p className="text-xs text-muted-foreground">Up to 5 stars; tap left or right half of a star for half steps.</p>
              <StarRating value={rating} onChange={setRating} size="lg" />
            </div>

            <div className="space-y-2">
              <Label htmlFor="body">Review (optional)</Label>
              <Textarea
                id="body"
                placeholder="What did you think about this album?"
                value={body}
                onChange={(e) => setBody(e.target.value)}
                rows={5}
              />
            </div>

            <div className="flex items-center gap-2">
              <Checkbox
                id="relisten"
                checked={isRelisten}
                onCheckedChange={(checked) => setIsRelisten(checked === true)}
              />
              <Label htmlFor="relisten" className="text-sm cursor-pointer">
                This is a relisten
              </Label>
            </div>

            <Button type="submit" className="w-full" disabled={submitting || rating === 0}>
              {submitting ? "Submitting..." : editId ? "Update Review" : "Submit Review"}
            </Button>
          </form>
        </CardContent>
      </Card>
    </div>
  );
}
