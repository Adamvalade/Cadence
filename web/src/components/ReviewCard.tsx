"use client";

import { useState } from "react";
import Link from "next/link";
import Image from "next/image";
import { Heart, MoreHorizontal, Music, Pencil, Trash2 } from "lucide-react";
import { Card, CardContent } from "@/components/ui/card";
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";
import { Button } from "@/components/ui/button";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import StarRating from "@/components/StarRating";
import { api } from "@/lib/api";
import { useAuth } from "@/lib/auth";
import { cn } from "@/lib/utils";
import type { Review } from "@/lib/types";

interface ReviewCardProps {
  review: Review;
  showAlbum?: boolean;
  onDelete?: (reviewId: string) => void;
  onUpdate?: (review: Review) => void;
}

export default function ReviewCard({ review, showAlbum = true, onDelete, onUpdate }: ReviewCardProps) {
  const { user } = useAuth();
  const [liked, setLiked] = useState(review.liked_by_me);
  const [likeCount, setLikeCount] = useState(review.like_count);
  const [showDeleteDialog, setShowDeleteDialog] = useState(false);
  const [deleting, setDeleting] = useState(false);

  const isOwn = user?.id === review.user_id;

  const toggleLike = async (e: React.MouseEvent) => {
    e.preventDefault();
    try {
      if (liked) {
        await api.delete(`/reviews/${review.id}/like`);
        setLikeCount((c) => c - 1);
      } else {
        await api.post(`/reviews/${review.id}/like`);
        setLikeCount((c) => c + 1);
      }
      setLiked(!liked);
    } catch {
      // not authenticated or already liked/unliked
    }
  };

  const handleDelete = async () => {
    setDeleting(true);
    try {
      await api.delete(`/reviews/${review.id}`);
      setShowDeleteDialog(false);
      onDelete?.(review.id);
    } catch {
      setDeleting(false);
    }
  };

  const timeAgo = getTimeAgo(review.created_at);

  return (
    <>
      <Card>
        <CardContent className="p-4">
          <div className="flex gap-4">
            {showAlbum && (
              <Link href={`/album/${review.album_id}`} className="shrink-0">
                <div className="w-20 h-20 rounded-md overflow-hidden bg-muted relative">
                  {review.album_cover_url ? (
                    <Image
                      src={review.album_cover_url}
                      alt={review.album_title}
                      fill
                      className="object-cover"
                      sizes="80px"
                    />
                  ) : (
                    <div className="w-full h-full flex items-center justify-center">
                      <Music className="h-6 w-6 text-muted-foreground/40" />
                    </div>
                  )}
                </div>
              </Link>
            )}

            <div className="flex-1 min-w-0 space-y-2">
              <div className="flex items-start justify-between gap-2">
                <div className="min-w-0">
                  <div className="flex items-center gap-2">
                    <Link href={`/${review.username}`} className="flex items-center gap-1.5 hover:underline">
                      <Avatar className="h-5 w-5">
                        <AvatarImage src={review.user_avatar_url || undefined} />
                        <AvatarFallback className="text-[10px]">
                          {review.username[0].toUpperCase()}
                        </AvatarFallback>
                      </Avatar>
                      <span className="text-sm font-medium">{review.username}</span>
                    </Link>
                    <span className="text-xs text-muted-foreground">{timeAgo}</span>
                  </div>
                  {showAlbum && (
                    <Link href={`/album/${review.album_id}`} className="hover:underline">
                      <p className="text-sm mt-0.5">
                        <span className="font-medium">{review.album_title}</span>
                        <span className="text-muted-foreground"> by {review.album_artist}</span>
                      </p>
                    </Link>
                  )}
                </div>

                {isOwn && (
                  <DropdownMenu>
                    <DropdownMenuTrigger render={<Button variant="ghost" size="sm" className="h-7 w-7 p-0" />}>
                      <MoreHorizontal className="h-4 w-4" />
                    </DropdownMenuTrigger>
                    <DropdownMenuContent align="end">
                      <DropdownMenuItem onClick={() => window.location.href = `/album/${review.album_id}/review?edit=${review.id}`}>
                        <Pencil className="mr-2 h-3.5 w-3.5" />
                        Edit review
                      </DropdownMenuItem>
                      <DropdownMenuItem
                        className="text-destructive"
                        onClick={() => setShowDeleteDialog(true)}
                      >
                        <Trash2 className="mr-2 h-3.5 w-3.5" />
                        Delete review
                      </DropdownMenuItem>
                    </DropdownMenuContent>
                  </DropdownMenu>
                )}
              </div>

              <StarRating value={review.rating} size="sm" readonly />

              {review.body && (
                <p className="text-sm text-muted-foreground line-clamp-3">{review.body}</p>
              )}

              <div className="flex items-center gap-3">
                <Button variant="ghost" size="sm" className="h-7 px-2 gap-1" onClick={toggleLike}>
                  <Heart
                    className={cn("h-3.5 w-3.5", liked && "fill-red-500 text-red-500")}
                  />
                  <span className="text-xs">{likeCount}</span>
                </Button>
                {review.is_relisten && (
                  <span className="text-xs text-muted-foreground italic">relisten</span>
                )}
              </div>
            </div>
          </div>
        </CardContent>
      </Card>

      <Dialog open={showDeleteDialog} onOpenChange={setShowDeleteDialog}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Delete review</DialogTitle>
            <DialogDescription>
              Are you sure you want to delete your review of {review.album_title}? This cannot be undone.
            </DialogDescription>
          </DialogHeader>
          <DialogFooter>
            <Button variant="outline" onClick={() => setShowDeleteDialog(false)} disabled={deleting}>
              Cancel
            </Button>
            <Button variant="destructive" onClick={handleDelete} disabled={deleting}>
              {deleting ? "Deleting..." : "Delete"}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </>
  );
}

function getTimeAgo(dateString: string): string {
  const now = new Date();
  const date = new Date(dateString);
  const seconds = Math.floor((now.getTime() - date.getTime()) / 1000);

  if (seconds < 60) return "just now";
  const minutes = Math.floor(seconds / 60);
  if (minutes < 60) return `${minutes}m ago`;
  const hours = Math.floor(minutes / 60);
  if (hours < 24) return `${hours}h ago`;
  const days = Math.floor(hours / 24);
  if (days < 30) return `${days}d ago`;
  const months = Math.floor(days / 30);
  if (months < 12) return `${months}mo ago`;
  return `${Math.floor(months / 12)}y ago`;
}
