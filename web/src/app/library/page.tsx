"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import Image from "next/image";
import { Clock, Headphones, CheckCircle2, Library, Music } from "lucide-react";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Skeleton } from "@/components/ui/skeleton";
import { api } from "@/lib/api";
import { useAuth } from "@/lib/auth";

interface ListenStatusItem {
  id: string;
  album_id: string;
  status: string;
  album_title: string;
  album_artist: string;
  album_cover_url: string | null;
  created_at: string;
  updated_at: string;
}

const STATUS_CONFIG = {
  want_to_listen: { label: "Want to Listen", icon: Clock, color: "text-blue-500" },
  listening: { label: "Listening", icon: Headphones, color: "text-yellow-500" },
  listened: { label: "Listened", icon: CheckCircle2, color: "text-green-500" },
} as const;

function AlbumGrid({ items }: { items: ListenStatusItem[] }) {
  if (items.length === 0) {
    return <p className="text-muted-foreground text-center py-12">No albums here yet.</p>;
  }
  return (
    <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 gap-4">
      {items.map((item) => (
        <Link key={item.id} href={`/album/${item.album_id}`} className="group space-y-2">
          <div className="aspect-square rounded-lg overflow-hidden bg-muted relative">
            {item.album_cover_url ? (
              <Image
                src={item.album_cover_url}
                alt={item.album_title}
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
            <p className="text-sm font-medium truncate">{item.album_title}</p>
            <p className="text-xs text-muted-foreground truncate">{item.album_artist}</p>
          </div>
        </Link>
      ))}
    </div>
  );
}

function GridSkeleton() {
  return (
    <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 gap-4">
      {Array.from({ length: 10 }, (_, i) => (
        <div key={i} className="space-y-2">
          <Skeleton className="aspect-square rounded-lg" />
          <Skeleton className="h-4 w-3/4" />
          <Skeleton className="h-3 w-1/2" />
        </div>
      ))}
    </div>
  );
}

export default function LibraryPage() {
  const { user, loading: authLoading } = useAuth();
  const router = useRouter();
  const [items, setItems] = useState<Record<string, ListenStatusItem[]>>({
    want_to_listen: [],
    listening: [],
    listened: [],
  });
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (authLoading) return;
    if (!user) {
      router.push("/auth/login");
      return;
    }

    const load = async () => {
      const [wantResult, listeningResult, listenedResult] = await Promise.allSettled([
        api.get<ListenStatusItem[]>("/listen-status", { status: "want_to_listen" }),
        api.get<ListenStatusItem[]>("/listen-status", { status: "listening" }),
        api.get<ListenStatusItem[]>("/listen-status", { status: "listened" }),
      ]);
      setItems({
        want_to_listen: wantResult.status === "fulfilled" ? wantResult.value : [],
        listening: listeningResult.status === "fulfilled" ? listeningResult.value : [],
        listened: listenedResult.status === "fulfilled" ? listenedResult.value : [],
      });
      setLoading(false);
    };
    load();
  }, [user, authLoading, router]);

  if (authLoading || loading) {
    return (
      <div className="max-w-5xl mx-auto px-4 py-8">
        <div className="flex items-center gap-2 mb-6">
          <Library className="h-6 w-6" />
          <h1 className="text-2xl font-bold">My Library</h1>
        </div>
        <GridSkeleton />
      </div>
    );
  }

  const total = items.want_to_listen.length + items.listening.length + items.listened.length;

  return (
    <div className="max-w-5xl mx-auto px-4 py-8">
      <div className="flex items-center gap-2 mb-6">
        <Library className="h-6 w-6" />
        <h1 className="text-2xl font-bold">My Library</h1>
        <span className="text-sm text-muted-foreground ml-2">{total} albums</span>
      </div>

      <Tabs defaultValue="want_to_listen">
        <TabsList>
          <TabsTrigger value="want_to_listen" className="gap-1.5">
            <Clock className="h-3.5 w-3.5" />
            Want to Listen ({items.want_to_listen.length})
          </TabsTrigger>
          <TabsTrigger value="listening" className="gap-1.5">
            <Headphones className="h-3.5 w-3.5" />
            Listening ({items.listening.length})
          </TabsTrigger>
          <TabsTrigger value="listened" className="gap-1.5">
            <CheckCircle2 className="h-3.5 w-3.5" />
            Listened ({items.listened.length})
          </TabsTrigger>
        </TabsList>

        {(["want_to_listen", "listening", "listened"] as const).map((status) => (
          <TabsContent key={status} value={status} className="mt-6">
            <AlbumGrid items={items[status]} />
          </TabsContent>
        ))}
      </Tabs>
    </div>
  );
}
