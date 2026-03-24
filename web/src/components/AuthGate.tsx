"use client";

import { useEffect } from "react";
import { usePathname, useRouter } from "next/navigation";
import { useAuth } from "@/lib/auth";

function isPublicPath(pathname: string | null) {
  if (!pathname) return false;
  return pathname.startsWith("/auth/");
}

function AuthSpinner() {
  return (
    <div className="flex flex-1 flex-col items-center justify-center gap-2 py-12">
      <div className="h-7 w-7 animate-pulse rounded-full bg-primary/25" />
      <p className="text-xs text-muted-foreground">Loading…</p>
    </div>
  );
}

export function AuthGate({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const router = useRouter();
  const { user, loading } = useAuth();
  const publicPath = isPublicPath(pathname);
  const authFormPath = pathname === "/auth/login" || pathname === "/auth/register";

  useEffect(() => {
    if (loading) return;
    if (user && authFormPath) {
      router.replace("/feed");
      return;
    }
    if (!publicPath && !user) {
      router.replace("/auth/login");
    }
  }, [loading, publicPath, user, authFormPath, router]);

  if (publicPath && user && authFormPath) {
    return <AuthSpinner />;
  }

  if (!publicPath && (loading || !user)) {
    return <AuthSpinner />;
  }

  return <>{children}</>;
}
