"use client";

import Link from "next/link";
import { Music, Star, Users } from "lucide-react";
import { Button } from "@/components/ui/button";
import { useAuth } from "@/lib/auth";

export default function HomePage() {
  const { user } = useAuth();

  return (
    <div className="flex flex-col">
      <section className="flex flex-col items-center justify-center text-center py-24 px-4">
        <div className="flex items-center gap-3 mb-6">
          <Music className="h-10 w-10" />
          <h1 className="text-5xl font-bold tracking-tight">Cadence</h1>
        </div>
        <p className="text-xl text-muted-foreground max-w-lg mb-8">
          Track albums you&apos;ve listened to. Rate and review them. See what your friends are into.
        </p>
        {user ? (
          <div className="flex gap-3">
            <Button size="lg" render={<Link href="/feed" />}>Go to Feed</Button>
            <Button size="lg" variant="outline" render={<Link href="/search" />}>Search Albums</Button>
          </div>
        ) : (
          <div className="flex gap-3">
            <Button size="lg" render={<Link href="/auth/register" />}>Get Started</Button>
            <Button size="lg" variant="outline" render={<Link href="/auth/login" />}>Log In</Button>
          </div>
        )}
      </section>

      <section className="max-w-4xl mx-auto px-4 pb-24">
        <div className="grid md:grid-cols-3 gap-8">
          <div className="text-center space-y-3">
            <div className="mx-auto w-12 h-12 rounded-full bg-primary/10 flex items-center justify-center">
              <Music className="h-6 w-6" />
            </div>
            <h3 className="font-semibold text-lg">Log Albums</h3>
            <p className="text-sm text-muted-foreground">
              Search for any album via Spotify or add it manually. Build your listening history.
            </p>
          </div>
          <div className="text-center space-y-3">
            <div className="mx-auto w-12 h-12 rounded-full bg-primary/10 flex items-center justify-center">
              <Star className="h-6 w-6" />
            </div>
            <h3 className="font-semibold text-lg">Rate &amp; Review</h3>
            <p className="text-sm text-muted-foreground">
              Give albums a rating out of 10 and write reviews to share your thoughts.
            </p>
          </div>
          <div className="text-center space-y-3">
            <div className="mx-auto w-12 h-12 rounded-full bg-primary/10 flex items-center justify-center">
              <Users className="h-6 w-6" />
            </div>
            <h3 className="font-semibold text-lg">Follow Friends</h3>
            <p className="text-sm text-muted-foreground">
              Follow people and see their latest reviews in your personalized feed.
            </p>
          </div>
        </div>
      </section>
    </div>
  );
}
