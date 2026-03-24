"use client";

import Link from "next/link";
import { Music, Star, Users } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";

export default function HomePage() {
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
      <section className="relative px-3 pb-10 pt-10 sm:px-4 sm:pb-12 sm:pt-14">
        <div
          aria-hidden
          className="pointer-events-none absolute inset-0 overflow-hidden"
        >
          <div className="absolute left-1/2 top-0 h-[280px] w-[min(100%,560px)] -translate-x-1/2 rounded-full bg-primary/[0.1] blur-3xl dark:bg-primary/[0.16]" />
        </div>
        <div className="relative mx-auto flex max-w-2xl flex-col items-center text-center">
          <p className="mb-2 text-[0.65rem] font-medium uppercase tracking-[0.18em] text-muted-foreground">
            Your music, your circle
          </p>
          <h1 className="text-balance text-3xl font-semibold tracking-tight sm:text-4xl sm:leading-[1.12]">
            Log what you listen to.{" "}
            <span className="text-primary">Share</span> what it meant.
          </h1>
          <p className="mt-3 max-w-md text-pretty text-sm leading-relaxed text-muted-foreground sm:text-base">
            Track albums, rate and review them, and follow people to see their picks in one place.
          </p>
          <div className="mt-6 flex flex-wrap items-center justify-center gap-2">
            <Button className="min-w-[8.5rem] shadow-sm shadow-primary/10" render={<Link href="/feed" />}>
              Go to feed
            </Button>
            <Button variant="outline" render={<Link href="/search" />}>
              Search albums
            </Button>
          </div>
        </div>
      </section>

      <section className="mx-auto max-w-5xl px-3 pb-12 sm:px-5 sm:pb-16">
        <div className="grid gap-3 sm:grid-cols-3 sm:gap-3">
          {features.map(({ icon: Icon, title, body }) => (
            <Card
              key={title}
              className="border-border/60 bg-card/60 py-3.5 shadow-none backdrop-blur-sm transition-colors hover:bg-card/90"
            >
              <CardContent className="flex flex-col items-center gap-2 px-4 text-center sm:items-start sm:text-left">
                <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-primary/12 text-primary ring-1 ring-primary/15">
                  <Icon className="h-4 w-4" strokeWidth={1.75} />
                </div>
                <h3 className="text-sm font-medium tracking-tight">{title}</h3>
                <p className="text-xs leading-relaxed text-muted-foreground sm:text-sm">{body}</p>
              </CardContent>
            </Card>
          ))}
        </div>
      </section>
    </div>
  );
}
