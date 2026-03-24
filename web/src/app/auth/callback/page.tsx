"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { Loader2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import { useAuth } from "@/lib/auth";
import { persistAccessToken } from "@/lib/sessionToken";

export default function OAuthCallbackPage() {
  const { refresh } = useAuth();
  const router = useRouter();
  const [error, setError] = useState(false);

  useEffect(() => {
    const hash = typeof window !== "undefined" ? window.location.hash : "";
    if (hash.startsWith("#access_token=")) {
      const token = decodeURIComponent(hash.slice("#access_token=".length));
      if (token) {
        persistAccessToken(token);
        window.history.replaceState(null, "", `${window.location.pathname}${window.location.search}`);
      }
    }

    refresh()
      .then(() => router.push("/feed"))
      .catch(() => setError(true));
  }, [refresh, router]);

  if (error) {
    return (
      <div className="flex flex-col items-center justify-center min-h-[calc(100vh-3rem)] gap-3 px-4 py-8">
        <p className="text-destructive font-medium">Sign in failed</p>
        <p className="text-sm text-muted-foreground">Something went wrong during authentication.</p>
        <Button variant="outline" render={<Link href="/auth/login" />}>Back to login</Button>
      </div>
    );
  }

  return (
    <div className="flex flex-col items-center justify-center min-h-[calc(100vh-3rem)] gap-3 px-4 py-8">
      <Loader2 className="h-8 w-8 animate-spin" />
      <p className="text-muted-foreground">Completing sign in...</p>
    </div>
  );
}
