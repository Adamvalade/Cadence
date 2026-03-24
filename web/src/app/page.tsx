"use client";

import Link from "next/link";
import { Music, Star, Users } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { useAuth } from "@/lib/auth";

export default function HomePage() {
  const { user } = useAuth();

  const features = [
    {
      icon: Music,
      title: "Log albums",
      body: "Search via Spotify or add manually and build a listening history you actually use.",
    },
    {
      icon: Star,
      title: "Rate & review",
      body: "Score albums out of 10 and write reviews that show up for people who follow you.",
    },
    {
      icon: Users,
      title: "Follow friends",
      body: "See what others are into in a feed built from real activity, not algorithms.",
    },
  ] as const;

  return (
    <div className="flex flex-col">
      <section className="relative px-4 pb-16 pt-20 sm:pb-20 sm:pt-28">
        <div
          aria-hidden
          className="pointer-events-none absolute inset-0 overflow-hidden"
        >
          <div className="absolute left-1/2 top-0 h-[420px] w-[min(100%,720px)] -translate-x-1/2 rounded-full bg-primary/[0.12] blur-3xl dark:bg-primary/[0.18]" />
        </div>
        <div className="relative mx-auto flex max-w-2xl flex-col items-center text-center">
          <p className="mb-4 text-xs font-medium uppercase tracking-[0.2em] text-muted-foreground">
            Your music, your circle
          </p>
          <h1 className="text-balance text-4xl font-semibold tracking-tight sm:text-5xl sm:leading-[1.1]">
            Log what you listen to.{" "}
            <span className="text-primary">Share</span> what it meant.
          </h1>
          <p className="mt-5 max-w-md text-pretty text-base leading-relaxed text-muted-foreground sm:text-lg">
            Track albums, rate and review them, and follow people to see their picks in one place.
          </p>
          <div className="mt-10 flex flex-wrap items-center justify-center gap-3">
            {user ? (
              <>
                <Button size="lg" className="min-w-[9rem] shadow-sm shadow-primary/10" render={<Link href="/feed" />}>
                  Go to feed
                </Button>
                <Button size="lg" variant="outline" render={<Link href="/search" />}>
                  Search albums
                </Button>
              </>
            ) : (
              <>
                <Button size="lg" className="min-w-[9rem] shadow-sm shadow-primary/10" render={<Link href="/auth/register" />}>
                  Get started
                </Button>
                <Button size="lg" variant="outline" render={<Link href="/auth/login" />}>
                  Log in
                </Button>
              </>
            )}
          </div>
        </div>
      </section>

      <section className="mx-auto max-w-5xl px-4 pb-24 sm:px-6">
        <div className="grid gap-4 sm:grid-cols-3 sm:gap-5">
          {features.map(({ icon: Icon, title, body }) => (
            <Card
              key={title}
              className="border-border/60 bg-card/60 py-5 shadow-none backdrop-blur-sm transition-colors hover:bg-card/90"
            >
              <CardContent className="flex flex-col items-center gap-3 px-5 text-center sm:items-start sm:text-left">
                <div className="flex h-11 w-11 items-center justify-center rounded-xl bg-primary/12 text-primary ring-1 ring-primary/15">
                  <Icon className="h-5 w-5" strokeWidth={1.75} />
                </div>
                <h3 className="text-base font-medium tracking-tight">{title}</h3>
                <p className="text-sm leading-relaxed text-muted-foreground">{body}</p>
              </CardContent>
            </Card>
          ))}
        </div>
      </section>
    </div>
  );
}
