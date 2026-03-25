"use client";

import { useState } from "react";
import Link from "next/link";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { api } from "@/lib/api";
import { useTitle } from "@/lib/useTitle";

export default function ForgotPasswordPage() {
  useTitle("Forgot password");
  const [email, setEmail] = useState("");
  const [done, setDone] = useState(false);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    setLoading(true);
    try {
      await api.post("/auth/forgot-password", { email });
      setDone(true);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Something went wrong");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex items-center justify-center min-h-[calc(100vh-3rem)] px-3 py-6 sm:px-4">
      <Card className="w-full max-w-md border-border/70 shadow-sm">
        <CardHeader className="space-y-1 pb-3 text-center">
          <CardTitle className="text-xl">Forgot password</CardTitle>
          <CardDescription>We&apos;ll email you a link to reset it if this address has an account.</CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          {done ? (
            <p className="text-sm text-center text-muted-foreground">
              If that email is in our system, you will receive a link shortly. Check your spam folder.
            </p>
          ) : (
            <form onSubmit={handleSubmit} className="space-y-4">
              {error && (
                <div className="bg-destructive/10 text-destructive text-sm p-3 rounded-md">{error}</div>
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
              <Button type="submit" className="w-full" disabled={loading}>
                {loading ? "Sending…" : "Send reset link"}
              </Button>
            </form>
          )}
          <p className="text-center text-sm text-muted-foreground">
            <Link href="/auth/login" className="underline hover:text-foreground">
              Back to log in
            </Link>
          </p>
        </CardContent>
      </Card>
    </div>
  );
}
