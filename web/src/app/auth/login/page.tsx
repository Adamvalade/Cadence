"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Separator } from "@/components/ui/separator";
import { useAuth } from "@/lib/auth";
import { api } from "@/lib/api";
import { useTitle } from "@/lib/useTitle";

export default function LoginPage() {
  useTitle("Log in");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const [demoOffered, setDemoOffered] = useState<boolean | null>(null);
  const { login, demoLogin } = useAuth();
  const router = useRouter();

  useEffect(() => {
    let cancelled = false;
    api
      .get<{ enabled: boolean }>("/auth/demo-status")
      .then((r) => {
        if (!cancelled) setDemoOffered(r.enabled);
      })
      .catch(() => {
        // Still show the button: server may have demo on but status check failed (stale build, proxy, etc.).
        // demo-login returns a clear error if demo is off.
        if (!cancelled) setDemoOffered(true);
      });
    return () => {
      cancelled = true;
    };
  }, []);

  const demoHidden =
    process.env.NEXT_PUBLIC_DEMO_LOGIN === "false" || process.env.NEXT_PUBLIC_HIDE_DEMO === "true";
  const showDemo = !demoHidden && demoOffered === true;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    setLoading(true);
    try {
      await login(email, password);
      router.push("/feed");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Login failed");
    } finally {
      setLoading(false);
    }
  };

  const handleDemo = async () => {
    setError("");
    setLoading(true);
    try {
      await demoLogin();
      router.push("/feed");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Demo login failed");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex items-center justify-center min-h-[calc(100vh-3rem)] px-3 py-6 sm:px-4">
      <Card className="w-full max-w-md border-border/70 shadow-sm">
        <CardHeader className="space-y-1 pb-3 text-center">
          <CardTitle className="text-xl">Welcome back</CardTitle>
          <CardDescription>Log in to your Cadence account</CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          {showDemo && (
            <>
              <Button
                type="button"
                variant="secondary"
                className="w-full"
                disabled={loading}
                onClick={() => void handleDemo()}
              >
                {loading ? "Signing in…" : "Try demo (no signup)"}
              </Button>
              <p className="text-xs text-center text-muted-foreground leading-relaxed">
                Opens a shared account with sample friends, reviews, and likes so you can explore the app
                immediately.
              </p>
              <div className="flex items-center gap-3">
                <Separator className="flex-1" />
                <span className="text-xs text-muted-foreground">or email</span>
                <Separator className="flex-1" />
              </div>
            </>
          )}
          <form onSubmit={handleSubmit} className="space-y-4">
            {error && (
              <div className="bg-destructive/10 text-destructive text-sm p-3 rounded-md">
                {error}
              </div>
            )}
            <div className="space-y-2">
              <Label htmlFor="email">Email</Label>
              <Input
                id="email"
                type="email"
                placeholder="you@example.com"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                required
              />
            </div>
            <div className="space-y-2">
              <div className="flex items-center justify-between gap-2">
                <Label htmlFor="password">Password</Label>
                <Link
                  href="/auth/forgot-password"
                  className="text-xs text-muted-foreground underline hover:text-foreground"
                >
                  Forgot password?
                </Link>
              </div>
              <Input
                id="password"
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                autoComplete="current-password"
                required
              />
            </div>
            <Button type="submit" className="w-full" disabled={loading}>
              {loading ? "Logging in..." : "Log in"}
            </Button>
          </form>
          <p className="text-center text-sm text-muted-foreground mt-4">
            Don&apos;t have an account?{" "}
            <Link href="/auth/register" className="underline hover:text-foreground">
              Sign up
            </Link>
          </p>
        </CardContent>
      </Card>
    </div>
  );
}
