"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";
import { Loader2 } from "lucide-react";
import { useAuth } from "@/lib/auth";

export default function OAuthCallbackPage() {
  const { refresh } = useAuth();
  const router = useRouter();

  useEffect(() => {
    refresh().then(() => router.push("/feed"));
  }, [refresh, router]);

  return (
    <div className="flex flex-col items-center justify-center min-h-[calc(100vh-3.5rem)] gap-4">
      <Loader2 className="h-8 w-8 animate-spin" />
      <p className="text-muted-foreground">Completing sign in...</p>
    </div>
  );
}
