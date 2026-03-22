"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import Link from "next/link";
import Image from "next/image";
import { Loader2, Music } from "lucide-react";
import { api } from "@/lib/api";
import type { UserList } from "@/lib/types";

export default function ListDetailPage() {
  const { id } = useParams<{ id: string }>();
  const [list, setList] = useState<UserList | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    if (!id) return;
    api.get<UserList>(`/lists/${id}`)
      .then(setList)
      .catch((err) => setError(err instanceof Error ? err.message : "Failed to load list"))
      .finally(() => setLoading(false));
  }, [id]);

  if (loading) {
    return (
      <div className="flex justify-center py-24">
        <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
      </div>
    );
  }

  if (error || !list) {
    return (
      <div className="max-w-2xl mx-auto px-4 py-24 text-center">
        <h1 className="text-2xl font-bold">List not found</h1>
        <p className="text-muted-foreground mt-2">{error || "This list doesn't exist."}</p>
      </div>
    );
  }

  return (
    <div className="max-w-2xl mx-auto px-4 py-8">
      <h1 className="text-2xl font-bold">{list.title}</h1>
      {list.description && (
        <p className="text-muted-foreground mt-1">{list.description}</p>
      )}

      <div className="mt-6 space-y-2">
        {list.items.length === 0 ? (
          <p className="text-muted-foreground text-center py-8">This list is empty.</p>
        ) : (
          list.items.map((item, index) => (
            <Link
              key={item.id}
              href={`/album/${item.album_id}`}
              className="flex items-center gap-4 p-3 rounded-lg border hover:bg-accent/50 transition-colors"
            >
              <span className="text-sm font-medium text-muted-foreground w-6 text-right tabular-nums">
                {index + 1}
              </span>
              <div className="w-12 h-12 rounded-md overflow-hidden bg-muted relative shrink-0">
                {item.album_cover_url ? (
                  <Image
                    src={item.album_cover_url}
                    alt={item.album_title}
                    fill
                    className="object-cover"
                    sizes="48px"
                  />
                ) : (
                  <div className="w-full h-full flex items-center justify-center">
                    <Music className="h-4 w-4 text-muted-foreground/40" />
                  </div>
                )}
              </div>
              <div className="min-w-0 flex-1">
                <p className="font-medium text-sm truncate">{item.album_title}</p>
                <p className="text-xs text-muted-foreground truncate">{item.album_artist}</p>
              </div>
            </Link>
          ))
        )}
      </div>
    </div>
  );
}
